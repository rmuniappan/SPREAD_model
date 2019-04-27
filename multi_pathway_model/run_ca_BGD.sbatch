#!/bin/bash

# Example Slurm sbatch script for simple serial jobs in the discovery cluster
# discovery_q partition.

#
# SLURM JOB SCRIPT OPTIONS:
#
# The #SBATCH lines set various SLURM directive parameters for the job.
#
# The "#" sign in front of "SLURM" at the beginning of a sbatch script line is
# not a comment; Slurm interprets lines beginning with "#SBATCH" as denoting a
# job option directive.  All other instances of lines beginning with a "#" sign
# (including, e.g., "##SBATCH" and "# SBATCH") are comments as normal.
#
# It is important to keep all #SBATCH lines together near the top of the
# sbatch script.  No commands or variable settings should occur until
# after the #SBATCH lines. 

#
# REQUESTING RESOURCES:
#
# You will need to edit the --time resource limit line
# and the --nodes and --ntasks-per-node resource limits line
# to suit the requirements of your job.
#
# NOTE: --ntasks-per-node is equivalent to number of cores per node (and
#       therefore comparable to ppn in Torque), unless also specifying
#       a --cpus-per-task setting greater than 1.
#
# You may optionally request whole nodes by uncommenting the --exclusive line.
#
# You may optionally request memory required per node or memory required per
# allocated CPU by uncommenting and editing the --mem or --mem-per-cpu line.
#
# NOTE: The --mem parameter would generally be used if whole nodes are
#       allocated to jobs, while the --mem-per-cpu parameter would generally
#       be used if individual processors are allocated to jobs.


# Set the time, which is the maximum time your job can run in HH:MM:SS

#SBATCH --time=24:00:00


# Set the number of nodes, and the number of tasks per node (up to 16 per node)
#
# NOTE: The maximum number of tasks per node that can be requested will be
#       affected by the cpus per task setting if this setting is specified
#       with --cpus-per-task greater than 1.

#SBATCH --nodes=1 --ntasks-per-node=1


# If needed, request whole nodes by uncommenting the "#SBATCH --exclusive" line
# below

##SBATCH --exclusive


# If needed, request memory required per node or memory required per allocated
# CPU, in MegaBytes
#
# NOTE: Memory required per node would generally be used if whole nodes are
#       allocated to jobs, while memory required per allocated CPU would
#       generally be used if individual processors are allocated to jobs.
#
# NOTE: The commented out examples below show the currently configured default
#       values.

##SBATCH --mem=30464
##SBATCH --mem-per-cpu=1904


# Set the partition to submit to (a partition is equivalent to a queue)

#SBATCH -p discovery_q


# Optional: If modules are needed, source modules environment
#
# NOTE: This step is normally only needed for users whose default shell is
#       csh or tcsh.
#
# (Uncomment the following line if you wish to use it.)
# . /etc/profile.d/modules.sh

# Optional: Unload all loaded modulefiles, and then load the normal defaults
# (Uncomment the following lines if you wish to use them.)
# module purge
# . /etc/profile.d/user-default-modules.sh

# Load any modules you require:
#
# NOTE: The following example module "null" does nothing; replace the module
#       name with one you wish to load.
#
# (Uncomment the following line if you wish to use it.)
# module load null


# Below here enter the commands to start your job

module add Python/2.7.14-foss-2018a

python -u ../scripts/run_ca.py\
    --bgd \
    --grid_file $grid_file\
    --seed_file $seed_file\
    -o $out_file\
    -n $time_steps\
    --sim_runs $sim_runs\
    -s $start_month\
    -m $moore\
    --suitability_threshold $suit_thresh\
    --exp_delay $exp_delay\
    --alpha_sd $alpha_sd\
    --alpha_fm $alpha_fm\
    --alpha_mm $alpha_mm
