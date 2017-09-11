# run below in the python comsole
#>>> from notebook.auth import passwd
#>>> passwd('YOUR_SECRET_PASSWORD')
#'sha1:91d7cc9a1684:5597133e63270b3b693e2271d1b2434cd05c2e2d'

# copy the resulting sha1 code in below
screen -dmS notebook jupyter notebook --NotebookApp.password='sha1:THE_RESULTING_SHA1_CODE' --no-browser --port 5555 --ip='*'
