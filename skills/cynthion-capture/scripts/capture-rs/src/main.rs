// Copyright 2026 contributors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Cynthion USB Analyzer headless capture tool.
//
// Uses nusb (IOUSBHost on macOS) — same framework as Packetry, no sudo needed.
// Writes standard libpcap format (LINKTYPE_USB_2_0 = 288).
//
// Protocol reference: packetry src/backend/cynthion.rs
//   VID/PID:         0x1d50 / 0x615b
//   Analyzer iface:  class=0xFF sub=0x10 proto=0x01 (interface 0)
//   Bulk IN ep:      0x81, 16 KiB per transfer
//   Control req 1:   start/stop (Vendor|Interface, host->device)
//     value byte:    bits[2:1]=speed, bit[0]=enable
//     speed field:   0=HS-only  1=FS-only  2=LS-only  3=Auto (captures all)
//   Frame format:    [len_be:2][ts_be:2][data:len][pad_if_odd]
//   Event frame:     buf[0]==0xFF -> 4-byte header, no payload, skip

use std::fs::File;
use std::io::{BufWriter, Write};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

use futures_lite::future::block_on;
use nusb::transfer::{ControlOut, ControlType, Recipient, RequestBuffer};

const VID: u16 = 0x1d50;
const PID: u16 = 0x615b;
const ANALYZER_CLASS: u8 = 0xFF;
const ANALYZER_SUBCLASS: u8 = 0x10;
const ANALYZER_PROTOCOL: u8 = 0x01;
const BULK_EP_IN: u8 = 0x81;
const TRANSFER_SIZE: usize = 0x4000;
const CONCURRENT_TRANSFERS: usize = 4;

const PCAP_MAGIC: u32 = 0xa1b2c3d4;
const LINKTYPE_USB20: u32 = 288;

const REQ_CAPTURE: u8 = 1;

fn usage() -> ! {
    eprintln!("Usage: cynthion-capture [OPTIONS] <output.pcap>");
    eprintln!();
    eprintln!("Options:");
    eprintln!("  -d, --duration <seconds>   Stop after N seconds (default: run until Ctrl-C)");
    eprintln!("  -s, --speed <speed>        auto|hs|fs|ls  (default: auto)");
    eprintln!("  -h, --help                 Show this help");
    std::process::exit(1);
}

fn parse_args() -> (String, Option<f64>, u8) {
    let mut args = std::env::args().skip(1).peekable();
    let mut output: Option<String> = None;
    let mut duration: Option<f64> = None;
    let mut speed: u8 = 3;

    while let Some(arg) = args.next() {
        match arg.as_str() {
            "-h" | "--help" => usage(),
            "-d" | "--duration" => {
                let val = args.next().unwrap_or_else(|| usage());
                duration = Some(val.parse().unwrap_or_else(|_| {
                    eprintln!("invalid duration");
                    std::process::exit(1);
                }));
            }
            "-s" | "--speed" => {
                speed = match args.next().unwrap_or_default().as_str() {
                    "auto" => 3,
                    "hs" => 0,
                    "fs" => 1,
                    "ls" => 2,
                    other => {
                        eprintln!("unknown speed '{other}', use auto/hs/fs/ls");
                        std::process::exit(1);
                    }
                };
            }
            s if s.starts_with('-') => {
                eprintln!("unknown option: {s}");
                usage();
            }
            path => {
                output = Some(path.to_string());
            }
        }
    }
    (output.unwrap_or_else(|| usage()), duration, speed)
}

fn write_pcap_global_header(w: &mut impl Write) -> std::io::Result<()> {
    w.write_all(&PCAP_MAGIC.to_le_bytes())?;
    w.write_all(&2u16.to_le_bytes())?;
    w.write_all(&4u16.to_le_bytes())?;
    w.write_all(&0i32.to_le_bytes())?;
    w.write_all(&0u32.to_le_bytes())?;
    w.write_all(&65535u32.to_le_bytes())?;
    w.write_all(&LINKTYPE_USB20.to_le_bytes())?;
    Ok(())
}

fn write_pcap_record(w: &mut impl Write, data: &[u8]) -> std::io::Result<()> {
    let ts = SystemTime::now().duration_since(UNIX_EPOCH).unwrap();
    let ts_sec = ts.as_secs() as u32;
    let ts_usec = ts.subsec_micros();
    let n = data.len() as u32;
    w.write_all(&ts_sec.to_le_bytes())?;
    w.write_all(&ts_usec.to_le_bytes())?;
    w.write_all(&n.to_le_bytes())?;
    w.write_all(&n.to_le_bytes())?;
    w.write_all(data)?;
    Ok(())
}

fn send_capture_request(interface: &nusb::Interface, intf_num: u8, value: u8) {
    let _ = block_on(interface.control_out(ControlOut {
        control_type: ControlType::Vendor,
        recipient: Recipient::Interface,
        request: REQ_CAPTURE,
        value: value as u16,
        index: intf_num as u16,
        data: &[],
    }));
}

fn parse_and_write_frames(
    buf: &mut Vec<u8>,
    chunk: &[u8],
    writer: &mut impl Write,
    packets: &mut u64,
    bytes: &mut u64,
) -> std::io::Result<()> {
    buf.extend_from_slice(chunk);
    let mut pos = 0;
    while pos + 4 <= buf.len() {
        if buf[pos] == 0xFF {
            pos += 4;
            continue;
        }
        let pkt_len = ((buf[pos] as usize) << 8) | (buf[pos + 1] as usize);
        if pkt_len == 0 {
            pos += 1;
            continue;
        }
        let frame_end = pos + 4 + pkt_len + (pkt_len % 2);
        if frame_end > buf.len() {
            break;
        }
        let payload = &buf[pos + 4..pos + 4 + pkt_len];
        write_pcap_record(writer, payload)?;
        *packets += 1;
        *bytes += pkt_len as u64;
        pos = frame_end;
    }
    buf.drain(..pos);
    Ok(())
}

fn main() {
    let (output_path, duration_secs, speed) = parse_args();

    let speed_label = match speed {
        0 => "hs",
        1 => "fs",
        2 => "ls",
        _ => "auto",
    };
    let ctrl_start: u8 = (speed << 1) | 1;

    let di = nusb::list_devices()
        .expect("failed to list USB devices")
        .find(|d| d.vendor_id() == VID && d.product_id() == PID)
        .unwrap_or_else(|| {
            eprintln!("ERROR: No Cynthion USB Analyzer found.");
            eprintln!("  Check CONTROL port cable and run: cynthion run analyzer");
            std::process::exit(1);
        });

    let device = di.open().unwrap_or_else(|e| {
        eprintln!("ERROR: Failed to open device: {e}");
        std::process::exit(1);
    });

    let intf_info = device
        .active_configuration()
        .expect("failed to read configuration")
        .interface_alt_settings()
        .find(|i| {
            i.class() == ANALYZER_CLASS
                && i.subclass() == ANALYZER_SUBCLASS
                && i.protocol() == ANALYZER_PROTOCOL
        })
        .unwrap_or_else(|| {
            eprintln!("ERROR: Analyzer interface not found (class FF/10/01).");
            std::process::exit(1);
        });

    let intf_num = intf_info.interface_number();

    let interface = device.claim_interface(intf_num).unwrap_or_else(|e| {
        eprintln!("ERROR: Failed to claim interface {intf_num}: {e}");
        std::process::exit(1);
    });

    let running = Arc::new(AtomicBool::new(true));
    {
        let r = running.clone();
        ctrlc::set_handler(move || r.store(false, Ordering::Relaxed))
            .expect("failed to set Ctrl-C handler");
    }

    let file = File::create(&output_path).unwrap_or_else(|e| {
        eprintln!("ERROR: Cannot create {output_path}: {e}");
        std::process::exit(1);
    });
    let mut writer = BufWriter::new(file);
    write_pcap_global_header(&mut writer).expect("failed to write pcap header");

    send_capture_request(&interface, intf_num, ctrl_start);

    match duration_secs {
        Some(d) => eprintln!("Capturing ({speed_label}) -> {output_path} for {d:.1}s"),
        None => eprintln!("Capturing ({speed_label}) -> {output_path} -- Ctrl-C to stop"),
    }

    let deadline = duration_secs.map(|d| Instant::now() + Duration::from_secs_f64(d));

    let mut queue = interface.bulk_in_queue(BULK_EP_IN);
    for _ in 0..CONCURRENT_TRANSFERS {
        queue.submit(RequestBuffer::new(TRANSFER_SIZE));
    }

    let mut leftover: Vec<u8> = Vec::new();
    let mut total_packets: u64 = 0;
    let mut total_bytes: u64 = 0;

    loop {
        if !running.load(Ordering::Relaxed) {
            break;
        }
        if let Some(dl) = deadline {
            if Instant::now() >= dl {
                break;
            }
        }

        let completion = block_on(queue.next_complete());
        if completion.status.is_ok() {
            let _ = parse_and_write_frames(
                &mut leftover,
                &completion.data,
                &mut writer,
                &mut total_packets,
                &mut total_bytes,
            );
        }
        queue.submit(RequestBuffer::new(TRANSFER_SIZE));
    }

    send_capture_request(&interface, intf_num, 0);
    writer.flush().expect("failed to flush output");

    eprintln!("Done: {total_packets} packets, {total_bytes} bytes -> {output_path}");
}
