****************************************************************

Rollout	:      ROLLOUT_XXXX                               26-04-2017

Description: 

Issues Fixed: Issue(s) fixed, one per line.

****************************************************************

Release notes for the fixes in this rollout.

****************************************************************
            I N S T A L L A T I O N   N O T E S             
****************************************************************

1. Login as the environment's administrator.
2. Check for the below mentioned directories, create if not available
	$ cd $LESDIR/rollouts | if not available mkdir $LESDIR/rollouts
	$ mkdir ROLLOUT_XXXX
	
3. Traverse to temp directory in the local server 
	$ cd $LESDIR/temp
	$ mkdir $LESDIR/temp/ROLLOUT_XXXX
	$ cd $LESDIR/temp/ROLLOUT_XXXX
	
4. Copy the rollout distribution file into the environment's temporary directory and extract it as follows
	$ cp ROLLOUT_XXXX.tar $LESDIR/rollouts/ROLLOUT_XXXX/ROLLOUT_XXXX.tar
	$ cd $LESDIR/rollouts/ROLLOUT_XXXX
	$ tar xvf ROLLOUT_XXXX.tar

5. Shut down the RP environment.
	$ rp stop
	
6. Install the rollout.
	$ perl rollout.pl ROLLOUT_XXXX

7.  Start up the environment.
    $ rp start

