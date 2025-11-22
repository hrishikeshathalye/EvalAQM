#install ditg
sudo apt install d-itg
#install irtt
sudo apt install irtt
#install netserver dependency
sudo apt install netperf
#update and reinstall flent
cd flent
git checkout myflent
git pull origin myflent
sudo make
sudo make install
cd -
#install node and npm
cd $HOME
sudo apt install curl
curl -sL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs
sudo apt install npm
cd -
#install http-getter
cd ..
git clone git@github.com:tohojo/http-getter.git
cd http-getter
sudo apt install libcurl4-openssl-dev
sudo make
sudo make install
cd ../EvalAQM
#install mininet
cd ..
git clone git://github.com/mininet/mininet
cd mininet
sudo util/install.sh -a
cd ../EvalAQM
#install gnuplot
sudo apt install gnuplot
#install the project
sudo chmod +x -R scripts
echo "Install Completed Successfully"
