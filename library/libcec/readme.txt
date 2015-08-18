How 

https://drgeoffathome.wordpress.com/2015/08/09/a-premade-libcec-deb/comment-page-1/#comment-123


I’ve run across people who are interested in using libcec and 
would prefer to get started as soon as possible rather than
going down the compile it up route.  For those people, you can
download gzipped deb files from

http://www.owltra.com/libcec/index.html

A prerequisite is to have liblockdev1 installed.
-----------------------------------------
sudo apt-get install liblockdev1
-----------------------------------------


Then gunzip the deb file and install
-----------------------------------------
cd Downloads 
gunzip libcec_20150809-1_armhf.deb.gz 
sudo dpkg -i libcec_20150809-1_armhf.deb 
sudo ldconfig
----------------------------------------

