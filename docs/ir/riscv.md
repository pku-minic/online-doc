# 4.4. 将 Tigger 转换为 RISC-V 汇编

Tigger 在设计上考虑了 RISC-V 架构的特点, 所以你可以使用 “查表转换” 的方式直接将 Tigger 转换为 RISC-V 汇编.

我们建议, 在执行这步转换之前, 也就是在进行寄存器分配并生成 Tigger 的时候, 你的编译器可以保留一到两个寄存器 (例如 `t0`) 作为临时寄存器, 以便于在进行这步转换的时候临时存放一些中间结果.

## 转换规则

### 函数声明

如下的 Tigger **函数声明**:

```tigger
f_func [int1] [int2]

  ...

end f_func
```

应当被转换为:

```asm
  .text
  .align  2
  .global func
  .type   func, @function
func:
  addi    sp, sp, -STK
  sw      ra, STK-4(sp)

  ...

  .size   func, .-func
```

其中, `STK = (int2 / 4 + 1) * 16`.

例如:

```tigger
f_main [0] [17]

  ...

end f_main
```

应当被转换为:

```asm
  .text
  .align  2
  .global main
  .type   main, @function
main:
  addi    sp, sp, -80
  sw      ra, 76(sp)

  ...

  .size   main, .-main
```

此时的 `STK = (17 / 4 + 1) * 16 = 80`.

### 全局变量声明

如下的 Tigger **全局变量声明**:

```tigger
global_var = int
```

应当被转换为:

```asm
  .global   global_var
  .section  .sdata
  .align    2
  .type     global_var, @object
  .size     global_var, 4
global_var:
  .word     int
```

例如:

```tigger
v0 = 123
```

应当被转换为:

```asm
  .global   v0
  .section  .sdata
  .align    2
  .type     v0, @object
  .size     v0, 4
v0:
  .word     123
```

### 全局数组声明

如下的 Tigger **全局数组声明**:

```tigger
global_var = malloc int
```

应当被转换为:

```asm
  .comm global_var, int, 4
```

例如:

```tigger
v2 = malloc 800012
```

应当被转换为:

```asm
  .comm v2, 800012, 4
```

### 其他语句/表达式

假设寄存器 `t0` 在之前的阶段中未被分配给任何变量.

> 在你的编译器中, 这个寄存器需要由你自行控制.
>
> 如果你在评测系统中进行第三阶段 (Tigger 到 RISC-V) 的评测, 那么这个寄存器是 `s0`.

| Tigger                | RISC-V 汇编                                                  |
| ---                   | ---                                                         |
| reg = int             | li reg, int                                                 |
| reg1 = reg2 + reg3    | add reg1, reg2, reg3                                        |
| reg1 = reg2 - reg3    | sub reg1, reg2, reg3                                        |
| reg1 = reg2 * reg3    | mul reg1, reg2, reg3                                        |
| reg1 = reg2 / reg3    | div reg1, reg2, reg3                                        |
| reg1 = reg2 % reg3    | rem reg1, reg2, reg3                                        |
| reg1 = reg2 < reg3    | slt reg1, reg2, reg3                                        |
| reg1 = reg2 > reg3    | sgt reg1, reg2, reg3                                        |
| reg1 = reg2 <= reg3   | sgt reg1, reg2, reg3<br>not reg1, reg1                      |
| reg1 = reg2 >= reg3   | slt reg1, reg2, reg3<br>not reg1, reg1                      |
| reg1 = reg2 && reg3   | snez reg2, reg2<br>snez reg3, reg3<br>and reg1, reg2, reg3  |
| reg1 = reg2 \|\| reg3 | or reg1, reg2, reg3<br>snez reg1, reg1                      |
| reg1 = reg2 != reg3   | xor reg1, reg2, reg3<br>snez reg1, reg1                     |
| reg1 = reg2 == reg3   | xor reg1, reg2, reg3<br>seqz reg1, reg1                     |
| reg1 = reg2 + int12   | addi reg1, reg2, int12                                      |
| reg1 = reg2 < int12   | slti reg1, reg2, int12                                      |
| reg1 = reg2 op int    | li t0, int<br>op reg1, reg2, t0                             |
| reg1 = reg2           | mv reg1, reg2                                               |
| reg1[int12] = reg2    | sw reg2, int12(reg1)                                        |
| reg1 = reg2[int12]    | lw reg1, int12(reg2)                                        |
| if reg1 < reg2 goto label   | blt reg1, reg2, .label                                |
| if reg1 > reg2 goto label   | bgt reg1, reg2, .label                                |
| if reg1 <= reg2 goto label  | ble reg1, reg2, .label                                |
| if reg1 >= reg2 goto label  | bge reg1, reg2, .label                                |
| if reg1 != reg2 goto label  | bne reg1, reg2, .label                                |
| if reg1 == reg2 goto label  | beq reg1, reg2, .label                                |
| goto label                  | j .label                                              |
| label:                      | .label:                                               |
| call f_func                 | call func                                             |
| return                      | lw ra, STK-4(sp)<br>addi sp, sp, STK<br>ret           |
| store reg int10             | sw reg, int10*4(sp)                                   |
| load int10 reg              | lw reg, int10*4(sp)                                   |
| load global_var reg     | lui reg, %hi(global_var)<br>lw reg, %lo(global_var)(reg)  |
| loadaddr int10 reg      | addi reg, sp, int10*4                                     |
| loadaddr global_var reg | la reg, global_var                                        |

关于上表中的一些记法:

* `int`: 任意 32 位整数.
* `int12`: 任意有符号的 12 位整数, 即大于等于 -2048, 小于等于 2047 的整数. 如果数值超过该范围, 请先使用 `li` 伪指令将该整数加载到 `t0` 中, 然后再使用以 `t0` 寄存器作为操作数的指令执行相同操作.
* `int10`: 任意有符号的 10 位整数, 即大于等于 -512, 小于等于 511 的整数. 如果数值超过该范围, 请先使用 `li` 伪指令将该整数加载到 `t0` 中, 然后再使用以 `t0` 寄存器作为操作数的指令执行相同操作.
* `op`: 泛指要执行的操作, 请参考表中的其他项将其替换为对应的操作.
* `STK`: 同前文[函数声明](ir/riscv.md?id=函数声明)部分的 `STK`.

## 示例

Tigger 程序:

```tigger
v0 = 0
v1 = malloc 40

f_main [0] [0]
  call f_getint
  loadaddr v0 t0
  t0[0] = a0
  load v0 t0
  t1 = 10
  if t0 <= t1 goto l0
  a0 = 1
  return
l0:
  s0 = 0
  s1 = s0
l1:
  load v0 t0
  if s0 >= t0 goto l2
  call f_getint
  t0 = a0
  t1 = 4
  t2 = s0 * t1
	loadaddr v1 t3
	t3 = t3 + t2
  t3[0] = t0
  t4 = t3[0]
  s1 = s1 + t4
  s0 = s0 + 1
  goto l1
l2:
  a0 = s1
  call f_putint
  a0 = 0
  return
end f_main
```

转换得到的 RISC-V 汇编:

```asm
  .global   v0
  .section  .sdata
  .align    2
  .type     v0, @object
  .size     v0, 4
v0:
  .word     0
  .comm     v1, 40, 4

  .text
  .align    2
  .global   main
  .type     main, @function
main:
  addi      sp, sp, -16
  sw        ra, 12(sp)
  call      getint
  la        t0, v0
  sw        a0, 0(t0)
  lui       t0, %hi(v0)
  lw        t0, %lo(v0)(t0)
  li        t1, 10
  ble       t0, t1, .l0
  li        a0, 1
  lw        ra, 12(sp)
  addi      sp, sp, 16
  ret
.l0:
  li        s0, 0
  mv        s1, s0
.l1:
  lui       t0, %hi(v0)
  lw        t0, %lo(v0)(t0)
  bge       s0, t0, .l2
  call      getint
  mv        t0, a0
  li        t1, 4
  mul       t2, s0, t1
  la        t3, v1
  add       t3, t3, t2
  sw        t0, 0(t3)
  lw        t4, 0(t3)
  add       s1, s1, t4
  addi      s0, s0, 1
  j         .l1
.l2:
  mv        a0, s1
  call      putint
  li        a0, 0
  lw        ra, 12(sp)
  addi      sp, sp, 16
  ret
  .size     main, .-main
```

注意, 上述转换并不唯一, 你可以在 Tigger 转换到 RISC-V 汇编的过程中进行额外的优化, 从而得到性能更高/体积更小的指令序列.

## 运行/调试生成的 RISC-V 汇编

啊

## 常见问题

啊
