import argparse
import os.path
import logging
import pickle
import itertools
import re
import joblib
from dropy.web_utils import sync as sync_
from dropy.web_utils import list_folder
from dropy.updown.utils import unnest
from dropy import DropboxDownloader

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def match_files_to_patterns(folder, files, patterns):
    keep_files = []
    for file in files:
        for pattern in patterns:
            try:
                if re.match(pattern, file):
                    filename = file.replace(folder, "")
                    logger.debug(f"{file} -> {filename}")
                    keep_files.append(
                        filename
                    )
                    break
            except:
                continue

    return keep_files


def sanitize_path(path):
    while "//" in path:
        path = path.replace("//", "/")
    return path


def sync(src, dst, *args, **kwargs):
    src = sanitize_path(src)
    dst = sanitize_path(dst)
    logger.info(f"{src} -> {dst}")
    print(f"{src} -> {dst}")
    return sync_(src, dst, *args, **kwargs)


def generate_analysis_patterns(folder, session):

    files = [
        os.path.join(folder, f"session_{session}_error.txt"),
        os.path.join(folder, f"session_{session}/video_object.npy"),
        os.path.join(folder, f"session_{session}/preprocessing/blobs_collection_no_gaps.npy"),
        os.path.join(folder, f"session_{session}/preprocessing/blobs_collection.npy"),
        os.path.join(folder, f"session_{session}/preprocessing/fragments.npy"),
        os.path.join(folder, f"session_{session}/trajectories/trajectories.npy"),
        os.path.join(folder, f"session_{session}/trajectories/trajectories_wo_gaps.npy"),
    ]

    return files


def generate_imgstore_meta_patterns(folder, session):

    files = [
        os.path.join(folder, "metadata.yaml"),
        os.path.join(folder, f"{session}.extra.json"),
        os.path.join(folder, f"{session}.npz"),
        os.path.join(folder, f"{session}.png"),
    ]

    return files


PATTERNS = {
    "analysis": generate_analysis_patterns,
    "imgstore_meta": generate_imgstore_meta_patterns,
}


def list_files_one_session(file_type, folder, session):
    session_padded = str(session).zfill(6)
    files = PATTERNS[file_type](folder, session_padded)
    return files


def list_files_from_dropbox(*args, **kwargs):
    res = list_folder(*args, **kwargs)
    files = res["paths"]
    return files

def download_results(file_type, rootdir, folder, version=2, ncores=-2, sessions=None):
    """
    Downloads the idtrackerai results stored in Dropbox
    """

    assert rootdir.startswith("/")
    assert folder.startswith("/")

    folder_display = folder.replace("/./", "/")
    subfolder = folder.split("/./")
    if len(subfolder) == 1:
        subfolder = ""
    else:
        subfolder = subfolder[1]

    assert "/./" not in folder_display
    if version == 1:
        analysis_folder = folder_display
    elif version == 2:
        analysis_folder = os.path.jon(folder_display, "idtrackerai")

    patterns = PATTERNS[file_type](analysis_folder, "[0-9]{6}")


    if sessions is None:
        files = list_files_from_dropbox(folder_display, recursive=True)
    else:
        files = list(itertools.chain(*[list_files_one_session(file_type, folder_display, session) for session in sessions]))

    keep_files = match_files_to_patterns(folder_display, files, patterns)

    if len(keep_files) == 0:
        logger.warning(f"No files matching patterns in {folder_display}")
        return
    logger.debug(f"Files to be downloaded: {keep_files}")

    sync_args = [
        (f"Dropbox:{folder_display}/{file}", os.path.join(rootdir, subfolder, file.lstrip("/")))
        for file in keep_files
    ]

    with open("sync_args.pickle", "wb") as filehandle:
        pickle.dump(sync_args, filehandle)

    if ncores == 1:
        for arg in sync_args:
            sync(*arg, download=True)
    else:
        joblib.Parallel(n_jobs=ncores)(
            joblib.delayed(sync)(
                *arg, download=True
            )
                for arg in sync_args
        )


def get_parser(ap=None):
    if ap is None:
        ap = argparse.ArgumentParser()

    ap.add_argument("--rootdir", required=True)
    ap.add_argument("--folder", required=True)
    ap.add_argument("--version", default=2, type=int)
    ap.add_argument("--ncores", default=-2, type=int)
    ap.add_argument("--sessions", nargs="+", default=None, type=int)
    ap.add_argument("--file-type", dest="file_type")
    return ap


def main(args=None):

    if args is None:
        ap = get_parser()
        args = ap.parse_args()

    if args.sessions is None:
        sessions = None
    else:
        assert len(args.sessions) == 2
        sessions = list(range(*args.sessions))

    download_results(
        file_type=args.file_type,
        rootdir = args.rootdir,
        folder = args.folder,
        version=args.version,
        ncores=args.ncores,
        sessions=sessions,
    )

if __name__ == "__main__":
    main()
