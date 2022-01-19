# Lv1. `main` 函数

本章中, 你将实现一个能处理 `main` 函数和 `return` 语句的编译器. 你的编译器会将如下的 SysY 程序:

```clike
int main() {
  // 注释也应该被删掉哦
  return 0;
}
```

编译为对应的 Koopa IR:

```koopa
fun @main(): i32 {
%entry:
  ret 0
}
```
