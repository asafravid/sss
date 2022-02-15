dd if=/dev/zero of=swapfile_new_$1 bs=1024 count=8388608
mkswap swapfile_new_$1 
swapon -a swapfile_new_$1 
swapon -s

