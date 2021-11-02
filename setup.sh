cd ditg/src
sudo make install
cd -
if [ -d "flent" ] 
then
	cd flent
	git pull origin myflent
else
	git clone -b myflent git@github.com:hrishikeshathalye/flent.git
	cd flent
fi
sudo make install 
cd ..
