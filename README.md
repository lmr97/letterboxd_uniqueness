# letterboxd_uniqueness
This is a program to calculate the uniqueness of your ratings on the film review website Letterboxd, according to the following formula:

$$
u = \text {mean}(\frac{\bar{r} - r_u}{d_a})
$$

where

$\bar{r}$  is the average rating of a film, 

$r_u$  is the user's rating, and 

$d_a$  is the most a rating could differ from the average (a term I'm calling <i>available deviance</i>). It is defined as $d_a = \text {max}(\bar{r} - 0.5, 5 - \bar{r})$.


# Running the program
It's a very simple command line interface. Since its a Python program, you'll run it using the `python3` command. It takes a username as an argument on the command line, so place that at the end of the command. That gives the following on the command line, when you're in the directory you downloaded the program to:
```
python3 lbunique.py <username>
```
