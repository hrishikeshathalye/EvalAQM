#install ditg
cd ditg
git checkout master
git pull
cd src
sudo make
sudo make install
cd ../..
#update and reinstall flent
cd flent
git checkout myflent
git pull origin myflent
sudo make
sudo make install 
cd -
#get dash dataset
cd assets
sudo apt-get install lftp
lftp -c 'mirror --parallel=10 http://ftp.itec.aau.at/datasets/DASHDataset2014/BigBuckBunny/2sec/ ;exit'
mv 2sec bbb
cd -
#install the project
sudo pip install -r requirements.txt
echo "Install Completed Successfully"
