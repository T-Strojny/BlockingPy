"""Cotains the NNDBlocker class for blocking using the Nearest Neighbor Descent algorithm."""

import logging
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
import pynndescent

from .base import BlockingMethod


logger = logging.getLogger(__name__)


class NNDBlocker(BlockingMethod):
    """
    A blocker class that uses the Nearest Neighbor Descent (NND) algorithm.

    This class implements blocking functionality using the pynndescent library's 
    NNDescent algorithm for efficient approximate nearest neighbor search.

    Parameters
    ----------
    None

    Attributes
    ----------
    index : pynndescent.NNDescent or None
        The NNDescent index used for querying
    logger : logging.Logger
        Logger instance for outputting information and warnings

    See Also
    --------
    BlockingMethod : Abstract base class defining the blocking interface
    pynndescent.NNDescent : The underlying nearest neighbor descent implementation

    Notes
    -----
    For more details about the algorithm and implementation, see:
    https://pynndescent.readthedocs.io/en/latest/api.html
    https://github.com/lmcinnes/pynndescent
    """
    def __init__(self) -> None:
        """
        Initialize the NNDBlocker instance.

        Creates a new NNDBlocker with empty index and default logger settings.
        """
        self.index = None


    def block(self, x: pd.DataFrame, 
              y: pd.DataFrame, 
              k: int, 
              verbose: Optional[bool],
              controls: Dict[str, Any]) -> pd.DataFrame:
        """
        Perform blocking using the NND algorithm.

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
                'nnd': {
                    'metric': str,
                    'k_search': int,
                    'metric_kwds': dict,
                    'n_threads': int,
                    'tree_init': bool,
                    'n_trees': int,
                    'leaf_size': int,
                    'pruning_degree_multiplier': float,
                    'diversify_prob': float,
                    'init_graph': array-like or None,
                    'init_dist': array-like or None,
                    'low_memory': bool,
                    'max_candidates': int,
                    'max_rptree_depth': int,
                    'n_iters': int,
                    'delta': float,
                    'compressed': bool,
                    'parallel_batch_queries': bool,
                    'epsilon': float
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
            If an invalid distance metric is provided

        Notes
        -----
        The algorithm builds an approximate nearest neighbor index using 
        random projection trees and neighbor descent. The quality of the 
        approximation can be controlled through various parameters such 
        as n_trees, n_iters, and epsilon.
        """ 
        logger.setLevel(logging.INFO if verbose else logging.WARNING)

        distance = controls.get('nnd').get('metric')
        k_search = controls.get('nnd').get('k_search')

        if k_search > x.shape[0]:
            original_k_search = k_search
            k_search = min(k_search, x.shape[0])
            logger.warning(f"k_search ({original_k_search}) is larger than the number of reference points ({x.shape[0]}). Adjusted k_search to {k_search}.")
        
        logger.info(f"Initializing NND index with {distance} metric.")

        self.index = pynndescent.NNDescent(
            data=x,
            n_neighbors=k_search,
            metric=distance,
            metric_kwds=controls['nnd'].get('metric_kwds'),
            verbose=verbose,
            n_jobs=controls['nnd'].get('n_threads'),
            tree_init=controls['nnd'].get('tree_init'),
            n_trees=controls['nnd'].get('n_trees'),
            leaf_size=controls['nnd'].get('leaf_size'),
            pruning_degree_multiplier=controls['nnd'].get('pruning_degree_multiplier'),
            diversify_prob=controls['nnd'].get('diversify_prob'),
            init_graph=controls['nnd'].get('init_graph'),
            init_dist=controls['nnd'].get('init_dist'),
            #algorithm=nnd_params.get('algorithm'),
            low_memory=controls['nnd'].get('low_memory'),
            max_candidates=controls['nnd'].get('max_candidates'),
            max_rptree_depth=controls['nnd'].get('max_rptree_depth'),
            n_iters=controls['nnd'].get('n_iters'),
            delta=controls['nnd'].get('delta'),
            compressed=controls['nnd'].get('compressed'),
            parallel_batch_queries=controls['nnd'].get('parallel_batch_queries')
        )
        
        logger.info("Querying index...")
        
        l_1nn = self.index.query(
            query_data=y,
            k=k_search,
            epsilon=controls['nnd'].get('epsilon')
        )
        result = pd.DataFrame({
            'y': np.arange(y.shape[0]),
            'x': l_1nn[0][:, k-1],
            'dist': l_1nn[1][:, k-1]
        })

        logger.info("Process completed successfully.")

        return result
        