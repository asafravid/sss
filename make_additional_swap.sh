dd if=/dev/zero of=swapfile_new bs=1024 count=8388608
ls swapfile_new -ltr
mkswap swapfile_new 
swapon -a swapfile_new 
swapon -s

