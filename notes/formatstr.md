# 格式化字符串漏洞  
printf函数的返回值是输出字符的个数，输出失败时返回负值，  
- %d : 输出整数  
- %f : 输出浮点数  
- %c : 输出字符  
- %s : 输出字符串  
- %p : 输出16进制数（前面带0x）  
- %x : 输出16进制数（前面没有0x）  
- %n : 将之前打印出的字符个数赋值给一个变量  
- **%lln %n %hn %hhn分别表示向8，4，2，1字节的目标空间赋值**  
- %<number>$x : 获取第number个参数的值（%d，%p，%s等同样适用）  
出现printf(s)这样的就表示大概率有格式化字符串漏洞。  
一般遇到格式化字符串漏洞可以先将s赋值为aaaa-%p-%p-%p-%p这样的，通过观察
第几个%p输出了0x61616161的字样判断字符串所处的位置属于第几个参数  
测试结论，64位程序的格式化字符串参数从第一个开始依次选取rsi, , ,r8,r9