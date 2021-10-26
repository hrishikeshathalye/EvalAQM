sudo ln -s /etc/apparmor.d/usr.sbin.tcpdump /etc/apparmor.d/disable/
sudo apparmor_parser -R /etc/apparmor.d/disable/usr.sbin.tcpdump
sudo /etc/init.d/apparmor restart
