#install ditg
cd ditg
git pull
cd src
sudo make
sudo make install
cd ../..
#update and reinstall flent
cd flent
git pull origin myflent
sudo make
sudo make install 
cd -
#get dash dataset
cd assets
wget -r -nH -m --cut-dirs=4 ftp.itec.aau.at/datasets/DASHDataset2014/BigBuckBunny/2sec
mv 2sec bbb
cd -
#install the project
sudo pip install -r requirements.txt
echo "Install Completed Successfully"