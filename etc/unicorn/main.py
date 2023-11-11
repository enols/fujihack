from unicorn import *
from unicorn.arm_const import *
import sys, multiprocessing, os

MAX_MEM = 0x10000000

# Base addr of file, injected code should be
# position independent
BASE_ADDR = 0x0

start_inject = 0

def sanitizeString(e, addr):
    final = ""

    #if addr > 0x10000000:
    #    return "???"

    data = e.mem_read(addr, 100)
    for b in data:
        if b == 0:
            break
        elif b < 128:
            final += chr(b)
    return final

def printRegs(e, length):
    r0 = e.reg_read(UC_ARM_REG_R0)
    pc = e.reg_read(UC_ARM_REG_PC)
    lr = e.reg_read(UC_ARM_REG_LR)

    if pc >= start_inject:
        print("[I]   Custom PC: ", hex(pc - start_inject))
        os.system("arm-none-eabi-addr2line -e test.elf " + hex(pc - start_inject))

    if lr >= start_inject:
        print("[I]   Custom LR: ", hex(lr - start_inject))
        os.system("arm-none-eabi-addr2line -e test.elf " + hex(lr - start_inject))

    print("[I]   At PC:", hex(pc), "/", pc)
    print("[I]   In injection:", hex(pc - length), " inst #" + str((pc - length) / 4))
    print("[I]   LR:", hex(lr))
    print("[I]   R0:", hex(r0), "/", r0)
    print("[I]   R9:", hex(e.reg_read(UC_ARM_REG_R9)))
    print("[I]   Return String: '" + sanitizeString(e, r0) + "'")

def mmio_read(uc, offset, size, data):
    #printRegs(uc, 0)
    print("[I] Mirror memory read", hex(offset), size)
    return uc.mem_read(offset, data)

def mmio_write(uc, offset, size, value, data):
    print("[I] Mirror memory write", hex(offset), size)
    uc.mem_write(offset, value.to_bytes(size, byteorder="little"))

dbg_string = ""
def dbg_write(uc, offset, size, value, data):
    global dbg_string
    dbg_string += chr(value)
    if value == 0:
        print(">>>", dbg_string)
        dbg_string = ""

def dbg_read(uc, offset, size, value, data):
    print("IO Read")

def runEmu(e, start, end, firmware):
    try:
        e.emu_start(start, end, 0, 0)
    except UcError as err:
        print("[-] Unicorn error:", err)
        printRegs(e, len(firmware))
        return
    print("[+] Success.")
    printRegs(e, len(firmware))

def start():
    global start_inject
    e = Uc(UC_ARCH_ARM, UC_MODE_ARM)

    print("[I] Loading code...")
    fp = open(sys.argv[1], "rb")
    firmware = fp.read(60000000)
    print("[I] Firmware is", len(firmware), "bytes")

    print("[I] Allocating " + str(MAX_MEM / 1000 / 1000) + "mb memory...")
    e.mem_map(BASE_ADDR, MAX_MEM, UC_PROT_ALL)
    e.mem_write(BASE_ADDR, firmware)
    
    # Write test.o right after firmware
    start_inject = BASE_ADDR + len(firmware)
    fp = open("test.bin", "rb")
    injection = fp.read()
    e.mem_write(BASE_ADDR + len(firmware), injection)
    print("[I] Injection is", len(injection), "bytes")
    
    # Give the code some stack space, space it
    # away from code to limit interference
    e.reg_write(UC_ARM_REG_SP, len(firmware) + len(injection) + 128);
    e.reg_write(UC_ARM_REG_SB, 1);

    start = BASE_ADDR + len(firmware)
    end = BASE_ADDR + len(firmware) + len(injection)

    # Map 0x4* memory mirror
    e.mmio_map(0x40000000, 0x10000000, mmio_read, None, mmio_write, None)

    e.mmio_map(0x10000000, 1024, dbg_read, None, dbg_write, None)

    # Function returns to end
    e.reg_write(UC_ARM_REG_LR, end);

    print("[I] Starting emulator on new thread...")
    print("[I] Starting at", hex(start))
    p = multiprocessing.Process(target = runEmu,
        args = (e, start, end, firmware))
    p.start()
    p.join(20)
    if p.is_alive():
        print("[-] Thread timeout! Killing...")
        p.kill()
        return 1
    return 0

sys.exit(start())
