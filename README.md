# letterboxd_uniqueness
This is a program to calculate the uniqueness $u$ of your ratings on the film review website Letterboxd, according to the following formula:

$$
u = \text {mean}(\frac{|\bar{R} - R_u|}{D_a})
$$

where

&ensp; &ensp; $\bar{R}$ &ensp; is the site-wide average rating of a film, 

&ensp; &ensp; $R_u$ &ensp; is the user's rating of the film, and 

&ensp; &ensp; $D_a$ &ensp; is the most a rating could differ from the average (a term I'm calling <i>available deviance</i>). It is defined as $D_a = \text {max}(\bar{R} - 0.5,\space 5 - \bar{R})$.

This metric of uniqueness can be interpreted as "the user deviates $u$ of the amount they possibly could from average."

# Installing the program
Simply download the program from GitHub, and move it to where you like on your computer. There is no need to compile or build the program locally.

# Running the program
This program uses a very simple command line interface. Since it's a Python program, you'll run it using the `python3` command. It takes a username as an argument on the command line, so place that at the end of the command. This gives the following on the command line, when you're in the directory you downloaded the program to:
```
python3 lbunique.py <username>
```
