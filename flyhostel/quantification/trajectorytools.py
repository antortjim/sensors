import logging

import trajectorytools.trajectories.concatenate as concatenate

logger = logging.getLogger(__name__)

def get_trajectory_files(experiment_folder):

    trajectories = concatenate.get_trajectories(experiment_folder)#, allow_human=False)#, ignore_corrupt_chunks=True)
    trajectories_paths = [(k, v) for k, v in trajectories.items()]
    trajectories_paths = sorted(trajectories_paths, key=lambda x: x[0])
    trajectories_paths = [t[1] for t in trajectories_paths]
    trajectories_paths = [e for e in trajectories_paths if not "original" in e]
    return trajectories_paths


def load_trajectories(experiment_folder):
    trajectories_paths = get_trajectory_files(experiment_folder)
    status, tr = concatenate.from_several_idtracker_files(trajectories_paths, strict=False)
    logger.info("flyhostel has loaded", f"{(tr._s.shape[0]+2)/3600/12} hours of data successfully") # / seconds in hour and frames in second
    return status, tr