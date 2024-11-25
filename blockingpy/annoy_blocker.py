"""
Contains AnnnoyBlocker class for blocking using
Annoy algorithm from Spotify.
"""

import logging
import os
from tempfile import NamedTemporaryFile
from typing import Dict, Any, Optional

from annoy import AnnoyIndex
import numpy as np
import pandas as pd

from .base import BlockingMethod

logger = logging.getLogger(__name__)

class AnnoyBlocker(BlockingMethod):
    """
    A class for performing blocking using the Annoy algorithm.

    This class implements blocking functionality using Spotify's
    Annoy (Approximate Nearest Neighbors Oh Yeah) algorithm
    for efficient similarity search.

    Parameters
    ----------
    None

    Attributes
    ----------
    index : AnnoyIndex or None
        The Annoy index used for nearest neighbor search
    logger : logging.Logger
        Logger instance for the class
    x_columns : array-like or None
        Column names of the reference dataset
    METRIC_MAP : dict
        Mapping of distance metric names to their Annoy implementations

    See Also
    --------
    BlockingMethod : Abstract base class defining the blocking interface

    Notes
    -----
    For more details about the Annoy algorithm, see:
    https://github.com/spotify/annoy
    """
    METRIC_MAP: Dict[str, str] = {
        "euclidean": "euclidean",
        "manhattan": "manhattan",
        "hamming": "hamming",
        "angular": "angular"
    }

    def __init__(self) -> None:
        """
        Initialize the AnnoyBlocker instance.

        Creates a new AnnoyBlocker with empty index and default logger settings.
        """
        self.index: Optional[AnnoyIndex] = None
        self.x_columns = None
    
    def block(self, x: pd.DataFrame, 
              y: pd.DataFrame, 
              k: int,
              verbose: Optional[bool], 
              controls: Dict[str, Any]) -> pd.DataFrame:
        """
        Perform blocking using the Annoy algorithm.

        Parameters
        ----------
        x : pandas.DataFrame
            Reference dataset containing features for indexing
        y : pandas.DataFrame
            Query dataset to find nearest neighbors for
        k : int
            Number of nearest neighbors to find
        verbose : bool, optional
            If True, print detailed progress information
        controls : dict
            Algorithm control parameters with the following structure:
            {
                'annoy': {
                    'distance': str,
                    'seed': int,
                    'path': str,
                    'n_trees': int,
                    'build_on_disk': bool,
                    'k_search': int
                }
            }

        Returns
        -------
        pandas.DataFrame
            DataFrame containing the blocking results with columns:
            - 'y': indices from query dataset
            - 'x': indices of matched items from reference dataset
            - 'dist': distances to matched items

        Raises
        ------
        ValueError
            If an invalid distance metric is provided in controls or if path is provided but incorrect

        Notes
        -----
        The function builds an Annoy index from the reference dataset 
        and finds the k-nearest neighbors for each point in the query dataset.
        """

        logger.setLevel(logging.INFO if verbose else logging.WARNING)

        self.x_columns = x.columns

        distance = controls['annoy'].get('distance')
        verbose = verbose
        seed = controls['annoy'].get('seed')
        path = controls['annoy'].get('path')
        n_trees = controls['annoy'].get('n_trees')
        build_on_disk = controls['annoy'].get('build_on_disk')
        k_search = controls['annoy'].get('k_search')

        self._check_distance(distance)

        ncols = x.shape[1]
        metric = self.METRIC_MAP[distance]

        self.index = AnnoyIndex(ncols, metric)
        if seed is not None:
            self.index.set_seed(seed)

        if build_on_disk:
            if build_on_disk:
                with NamedTemporaryFile(prefix="annoy", suffix=".tree") as temp_file:
                    if verbose:
                        logger.info(f"Building index on disk: {temp_file.name}")
                    self.index.on_disk_build(temp_file.name)
        
        if verbose:
            self.index.verbose(True)

        logger.info("Building index...")

        for i in range(x.shape[0]):
            self.index.add_item(i, x.iloc[i].values)
        self.index.build(n_trees=n_trees)

        logger.info("Querying index...")

        l_ind_nns = np.zeros(y.shape[0], dtype=int)
        l_ind_dist = np.zeros(y.shape[0])

        if k_search > x.shape[0]:
            original_k_search = k_search
            k_search = min(k_search, x.shape[0])
            logger.warning(f"k_search ({original_k_search}) is larger than the number of reference points ({x.shape[0]}). Adjusted k_search to {k_search}.")
        
        for i in range(y.shape[0]):
            annoy_res = self.index.get_nns_by_vector(y.iloc[i].values, k_search, include_distances=True)
            l_ind_nns[i] = annoy_res[0][k-1]
            l_ind_dist[i] = annoy_res[1][k-1]

        if path:
            self._save_index(path)

        result = {
            'y': np.arange(y.shape[0]),
            'x': l_ind_nns,
            'dist': l_ind_dist,
        }

        result = pd.DataFrame(result)
        logger.info("Process completed successfully.")

        return result

    def _check_distance(self, distance: str) -> None:
        """
        Validate the provided distance metric.

        Parameters
        ----------
        distance : str
            The distance metric to validate

        Raises
        ------
        ValueError
            If the provided distance is not in the METRIC_MAP
        """
        if distance not in self.METRIC_MAP:
            valid_metrics = ", ".join(self.METRIC_MAP.keys())
            raise ValueError(f"Invalid distance metric '{distance}'. Accepted values are: {valid_metrics}.")
             
    def _save_index(self, path: str) -> None:
        """
        Save the Annoy index and column names to files.

        Parameters
        ----------
        path : str
            Directory path where the files will be saved
        verbose : bool
            If True, print information about the save operation
        
        Raises
        ------
        ValueError
            If the provided path is incorrect 

        Notes
        -----
        Creates two files:
            - 'index.annoy': The Annoy index file
            - 'index-colnames.txt': A text file with column names
        """
        if not os.path.exists(os.path.dirname(path)):
            raise ValueError("Provided path is incorrect")
        
        path_ann = os.path.join(path, "index.annoy")
        path_ann_cols = os.path.join(path, "index-colnames.txt")

        logger.info(f"Writing an index to {path_ann}")
        
        self.index.save(path_ann)

        with open(path_ann_cols, 'w') as f:
            f.write('\n'.join(self.x_columns))
