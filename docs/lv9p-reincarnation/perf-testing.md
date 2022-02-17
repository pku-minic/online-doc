# Lv9+.5. 性能测试

在 Lv9+.2, Lv9+.3 和 Lv9+.4 中, 你已经为你的编译器添加了很多新的实现, 来生成性能更高的代码. 编译实践的本地实验环境/在线评测系统均支持性能测试, 在完成各类优化后, 你可以进行性能测试, 来直观感受这些改进带来的性能提升.

## 本地测试

```
docker run -it --rm -v 项目目录:/root/compiler compiler-dev \
  autotest -perf -s perf /root/compiler
```

## 在线评测

?> **TODO:** 待补充.
