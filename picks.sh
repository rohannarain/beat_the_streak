cd ~/Desktop/datascience/beat_the_streak
/Users/rohannarain/anaconda3/bin/python retrieve_data.py
/Users/rohannarain/anaconda3/bin/python train_model.py
git add -A
git commit -m "predictions $(date +"%D")"
git push origin master