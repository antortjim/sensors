import logging
import itertools
import os.path
import glob
import numpy as np
import yaml

from imgstore.constants import STORE_MD_KEY, STORE_MD_FILENAME

logger = logging.getLogger(__name__)


INDEX_FORMAT=".npz"

def get_chunk_metadata(chunk_filename):

    data = np.load(chunk_filename)
    index = {}
    index["frame_time"] = data["frame_time"]
    index["frame_number"] = data["frame_number"]
    return index

def _read_store_metadata(imgstore_folder):
    metadata_filename = os.path.join(imgstore_folder, STORE_MD_FILENAME)
    with open(metadata_filename, "r") as filehandle:
        store_metadata = yaml.load(filehandle, Loader=yaml.SafeLoader)["__store"]
    
    return store_metadata


def read_store_metadata(imgstore_folder, chunk_numbers=None):

    store_metadata = _read_store_metadata(imgstore_folder)

    if chunk_numbers is None:
        index_files = sorted(
            glob.glob(
                os.path.join(
                    imgstore_folder,
                    f"*{INDEX_FORMAT}"
                )
            )
        )
        chunks = [
            int(os.path.basename(e.replace(INDEX_FORMAT, "")))
            for e in index_files
        ]   
    else:
        chunks = chunk_numbers
        index_files = [
            os.path.join(
                imgstore_folder,
                f"{str(chunk_index).zfill(6)}{INDEX_FORMAT}"
            )
            for chunk_index in chunks
        ]

    store_metadata["chunks"] = chunks

    chunk_metadata = {
        chunk: get_chunk_metadata(chunk) for chunk in index_files
    }

    frame_number = list(
        itertools.chain(*[m["frame_number"] for m in chunk_metadata.values()])
    )
    frame_time = list(
        itertools.chain(*[m["frame_time"] for m in chunk_metadata.values()])
    )

    chunk_metadata = (frame_number, frame_time)
    return store_metadata, chunk_metadata
