netsh advfirewall firewall add rule name="zhmr_udp" dir=in protocol=udp localport=46797 action=allow
netsh advfirewall firewall add rule name="zhmr_tcp" dir=in protocol=tcp localport=6797 action=allow
netsh advfirewall firewall add rule name="zhmr_ping" dir=in protocol=icmpv4 action=allow
echo 完事啦，可以联机了，可以关闭这个窗口了
pause