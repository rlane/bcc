#!/usr/bin/env python
# Copyright (c) PLUMgrid, Inc.
# Licensed under the Apache License, Version 2.0 (the "License")

from bcc import BPF
from unittest import main, TestCase

class TestClang(TestCase):
    def test_complex(self):
        b = BPF(src_file="test_clang_complex.c", debug=0)
        fn = b.load_func("handle_packet", BPF.SCHED_CLS)
    def test_printk(self):
        text = """
#include <bcc/proto.h>
int handle_packet(void *ctx) {
  u8 *cursor = 0;
  struct ethernet_t *ethernet = cursor_advance(cursor, sizeof(*ethernet));
  bpf_trace_printk("ethernet->dst = %llx, ethernet->src = %llx\\n",
                   ethernet->dst, ethernet->src);
  return 0;
}
"""
        b = BPF(text=text, debug=0)
        fn = b.load_func("handle_packet", BPF.SCHED_CLS)

    def test_probe_read1(self):
        text = """
#include <linux/sched.h>
#include <uapi/linux/ptrace.h>
int count_sched(struct pt_regs *ctx, struct task_struct *prev) {
    pid_t p = prev->pid;
    return (p != -1);
}
"""
        b = BPF(text=text, debug=0)
        fn = b.load_func("count_sched", BPF.KPROBE)

    def test_probe_read2(self):
        text = """
#include <linux/sched.h>
#include <uapi/linux/ptrace.h>
int count_foo(struct pt_regs *ctx, unsigned long a, unsigned long b) {
    return (a != b);
}
"""
        b = BPF(text=text, debug=0)
        fn = b.load_func("count_foo", BPF.KPROBE)

    def test_probe_read_keys(self):
        text = """
#include <uapi/linux/ptrace.h>
#include <linux/blkdev.h>
BPF_HASH(start, struct request *);
int do_request(struct pt_regs *ctx, struct request *req) {
    u64 ts = bpf_ktime_get_ns();
    start.update(&req, &ts);
    return 0;
}

int do_completion(struct pt_regs *ctx, struct request *req) {
    u64 *tsp = start.lookup(&req);
    if (tsp != 0) {
        start.delete(&req);
    }
    return 0;
}
"""
        b = BPF(text=text, debug=0)
        fns = b.load_funcs(BPF.KPROBE)

    def test_sscanf(self):
        text = """
BPF_TABLE("hash", int, struct { u64 a; u64 b; u64 c:36; u64 d:28; struct { u32 a; u32 b; } s; }, stats, 10);
int foo(void *ctx) {
    return 0;
}
"""
        b = BPF(text=text, debug=0)
        fn = b.load_func("foo", BPF.KPROBE)
        t = b.get_table("stats")
        s1 = t.key_sprintf(t.Key(2))
        self.assertEqual(s1, b"0x2")
        s2 = t.leaf_sprintf(t.Leaf(2, 3, 4, 1, (5, 6)))
        l = t.leaf_scanf(s2)
        self.assertEqual(l.a, 2)
        self.assertEqual(l.b, 3)
        self.assertEqual(l.c, 4)
        self.assertEqual(l.d, 1)
        self.assertEqual(l.s.a, 5)
        self.assertEqual(l.s.b, 6)

    def test_iosnoop(self):
        text = """
#include <linux/blkdev.h>
#include <uapi/linux/ptrace.h>

struct key_t {
    struct request *req;
};

BPF_TABLE("hash", struct key_t, u64, start, 1024);
int do_request(struct pt_regs *ctx, struct request *req) {
    struct key_t key = {};

    bpf_trace_printk("traced start %d\\n", req->__data_len);

    return 0;
}
"""
        b = BPF(text=text, debug=0)
        fn = b.load_func("do_request", BPF.KPROBE)

    def test_blk_start_request(self):
        text = """
#include <linux/blkdev.h>
#include <uapi/linux/ptrace.h>
int do_request(struct pt_regs *ctx, int req) {
    bpf_trace_printk("req ptr: 0x%x\\n", req);
    return 0;
}
"""
        b = BPF(text=text, debug=0)
        fn = b.load_func("do_request", BPF.KPROBE)

    def test_bpf_hash(self):
        text = """
BPF_HASH(table1);
BPF_HASH(table2, u32);
BPF_HASH(table3, u32, int);
"""
        b = BPF(text=text, debug=0)

if __name__ == "__main__":
    main()
