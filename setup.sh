#install ditg
sudo apt install d-itg
#update and reinstall flent
cd flent
git checkout myflent
git pull origin myflent
sudo make
sudo make install 
cd -
#install node and build dash libraries
cd $HOME
sudo apt install curl
curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash -
sudo apt install nodejs
sudo apt install npm
cd -
cd dash.js-master
sudo npm install
sudo npm run build
cd -
#get dash dataset
cd assets
if [[ ! -e bbb ]]; then
	sudo apt-get install lftp
	lftp -c 'mirror --parallel=10 http://ftp.itec.aau.at/datasets/DASHDataset2014/BigBuckBunny/2sec/ ;exit'
	mv 2sec bbb
fi
cd -
#install the project
sudo chmod +x -R scripts
sudo pip install -r requirements.txt
echo "Install Completed Successfully"
