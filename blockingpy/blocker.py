import numpy as np
import pandas as pd
import networkx as nx
from scipy import sparse
from typing import Optional, Union, List, Dict, Any
import logging
import itertools
from collections import OrderedDict

from .annoy_blocker import AnnoyBlocker
from .hnsw_blocker import HNSWBlocker
from .mlpack_blocker import MLPackBlocker
from .nnd_blocker import NNDBlocker
from .helper_functions import validate_input, validate_true_blocks
from .blocking_result import BlockingResult

class Blocker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def block(self, 
              #x: Union[np.ndarray, pd.DataFrame, sparse.csr_matrix],
              x,
              y: Optional[Union[np.ndarray, pd.DataFrame, sparse.csr_matrix]] = None,
              deduplication: bool = True,
              on: Optional[List[str]] = None,
              on_blocking: Optional[List[str]] = None,
              ann: str = "nnd",
              distance: Optional[str] = None,
              ann_write: Optional[str] = None,
              ann_colnames: Optional[List[str]] = None,
              true_blocks: Optional[pd.DataFrame] = None,
              verbose: int = 0,
              graph: bool = False,
              seed: int = 2023,
              n_threads: int = 1,
              control_txt: Dict[str, Any] = None,
              control_ann: Dict[str, Any] = None):
        
        if distance is None:
            distance = {  
                "nnd": "cosine",
                "hnsw": "cosine",
                "annoy": "angular",
                "lsh": None,
                "kd": None
            }.get(ann)

        validate_input(x, ann, distance, ann_write)

        if y is not None:
            deduplication = False
            y_default = False
            k = 1
        else :
            y_default = y
            y = x
            k = 2
        
        validate_true_blocks(true_blocks, deduplication)

        ### TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION
        ### TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION
        ### TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION
        ### TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION
        x_dtm = x
        y_dtm = y
        ### TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION
        ### TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION
        ### TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION
        ### TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION TOKENIZATION

        colnames_xy = np.intersect1d(x_dtm.columns, y_dtm.columns)

        if verbose in [1, 2]:
            print(f"===== starting search ({ann}, x, y: {x_dtm.shape[0]}, {y_dtm.shape[0]}, t: {len(colnames_xy)}) =====")

        if ann == 'nnd':
            blocker = NNDBlocker()
        elif ann == 'hnsw':
            blocker = HNSWBlocker()
        elif ann in ['lsh', 'kd']:
            blocker = MLPackBlocker()
        elif ann == 'annoy':
            blocker = AnnoyBlocker()
        
        x_df = blocker.block(
            x=x_dtm[:, colnames_xy],
            y=y_dtm[:, colnames_xy],
            k=k,
            verbose=True if verbose == 2 else False,
            controls=control_ann
            )
    
        if verbose in [1,2]:
            print("===== creating graph =====\n")
        
        if deduplication:
            x_df = x_df[x_df['y'] > x_df['x']]

            x_df['query_g'] = 'q' + x_df['y'].astype(str)
            x_df['index_g'] = 'q' + x_df['x'].astype(str)
        else:
            x_df['query_g'] = 'q' + x_df['y'].astype(str)
            x_df['index_g'] = 'i' + x_df['x'].astype(str)

        ### IGRAPH PART IN R
        x_gr = nx.from_pandas_edgelist(x_df, source='query_g', target='index_g', create_using=nx.Graph())
        components = nx.connected_components(x_gr)
        x_block = {}
        for component_id, component in enumerate(components):
            for node in component:
                x_block[node] = component_id

        unique_query_g = x_df['query_g'].unique()
        unique_index_g = x_df['index_g'].unique()
        combined_keys = list(unique_query_g) + [node for node in unique_index_g if node not in unique_query_g]

        sorted_dict = OrderedDict()
        for key in combined_keys:
            if key in x_block:
                sorted_dict[key] = x_block[key]

        x_df['block'] = x_df['query_g'].apply(lambda x: x_block[x] if x in x_block else None)
        ###

        if true_blocks is not None:
            if not deduplication:
                pairs_to_eval = x_df[x_df['y'].isin(true_blocks['y'])][['x','y','block']]
                pairs_to_eval = pairs_to_eval.merge(true_blocks[['x','y']],
                                                    on=['x','y'],
                                                    how='left',
                                                    indicator='both')
                pairs_to_eval['both'] = np.where(pairs_to_eval['both'] == 'both',0,-1)

                true_blocks = true_blocks.merge(pairs_to_eval[['x', 'y']], 
                                                on=['x', 'y'], 
                                                how='left', 
                                                indicator='both')
                true_blocks['both'] = np.where(true_blocks['both'] == 'both', 0, 1)
                true_blocks['block'] = true_blocks['block'] + pairs_to_eval['block'].max()

                to_concat = true_blocks[true_blocks['both'] == 1][['x', 'y', 'block', 'both']]
                pairs_to_eval = pd.concat([pairs_to_eval, to_concat], ignore_index=True)
                pairs_to_eval['row_id'] = range(len(pairs_to_eval))
                pairs_to_eval['x2'] = pairs_to_eval['x'] + pairs_to_eval['y'].max()

                pairs_to_eval_long = pd.melt(pairs_to_eval[['y', 'x2', 'row_id', 'block', 'both']],
                                            id_vars=['row_id', 'block', 'both'],
                                            )
                pairs_to_eval_long = pairs_to_eval_long[pairs_to_eval_long['both'] == 0]
                pairs_to_eval_long['block_id'] = pairs_to_eval_long.groupby('block').ngroup()
                pairs_to_eval_long['true_id'] = pairs_to_eval_long['block_id']

                block_id_max = pairs_to_eval_long['block_id'].max(skipna=True)
                pairs_to_eval_long.loc[pairs_to_eval_long['both'] == -1, 'block_id'] = block_id_max + pairs_to_eval_long.groupby('row_id').ngroup() + 1 
                block_id_max = pairs_to_eval_long['block_id'].max(skipna=True)
                # recreating R's rleid function
                pairs_to_eval_long['rleid'] = (pairs_to_eval_long['row_id'] != pairs_to_eval_long['row_id'].shift(1)).cumsum()
                pairs_to_eval_long.loc[(pairs_to_eval_long['both'] == 1) & (pairs_to_eval_long['block_id'].isna()), 'block_id'] = block_id_max + pairs_to_eval_long['rleid']

                true_id_max = pairs_to_eval_long['true_id'].max(skipna=True)
                pairs_to_eval_long.loc[pairs_to_eval_long['both'] == 1, 'true_id'] = true_id_max + pairs_to_eval_long.groupby('row_id').ngroup() + 1
                true_id_max = pairs_to_eval_long['treu_id'].max(skipna=True)
                # recreating R's rleid function again
                pairs_to_eval_long['rleid'] = (pairs_to_eval_long['row_id'] != pairs_to_eval_long['row_id'].shift(1)).cumsum()
                pairs_to_eval_long.loc[(pairs_to_eval_long['both'] == -1) & (pairs_to_eval_long['true_id'].isna()), 'true_id'] = true_id_max + pairs_to_eval_long['rleid']

                pairs_to_eval_long.drop('rleid', inplace=True)

            else:
                pairs_to_eval_long = (pd.melt(x_df[['x', 'y', 'block']], id_vars=['block'])
                      [['block', 'value']]
                      .drop_duplicates()
                      .rename(columns={'block': 'block_id', 'value': 'x'})
                      .merge(true_blocks[['x', 'block']], on='x', how='left')
                      .rename(columns={'block': 'true_id'}))
            
            candidate_pairs = np.fromiter(itertools.combinations(range(pairs_to_eval_long.shape[0]), 2), dtype=int).reshape(-1, 2)

            block_id_array = pairs_to_eval_long['block_id'].values
            true_id_array = pairs_to_eval_long['true_id'].values
            same_block = block_id_array[candidate_pairs[:, 0]] == block_id_array[candidate_pairs[:, 1]]
            same_truth = true_id_array[candidate_pairs[:, 0]] == true_id_array[candidate_pairs[:, 1]]

            confusion = pd.crosstab(same_block, same_truth)
            
            fp = confusion.loc[True, False]   
            fn = confusion.loc[False, True]   
            tp = confusion.loc[True, True]    
            tn = confusion.loc[False, False]  

            recall = tp / (fn + tp) if (fn + tp) != 0 else 0 
            precision = tp / (tp + fp) if (tp + fp) != 0 else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) != 0 else 0
            accuracy = (tp + tn) / (tp + tn + fp + fn)
            specificity = tn / (tn + fp) if (tn + fp) != 0 else 0
            fpr = fp / (fp + tn) if (fp + tn) != 0 else 0
            fnr = fn / (fn + tp) if (fn + tp) != 0 else 0

            eval_metrics = {
                'recall': recall,
                'precision': precision,
                'fpr': fpr,
                'fnr': fnr,
                'accuracy': accuracy,
                'specificity': specificity,
                'f1_score': f1_score,
            }
            eval_metrics = pd.Series(eval_metrics)
        
        x_df = x_df.sort_values(['x', 'y', 'block'])

        return BlockingResult(x_df=x_df,
                              ann=ann,
                              deduplication=deduplication,
                              true_blocks=true_blocks,
                              eval_metrics=eval_metrics,
                              confusion=confusion,
                              colnames_xy=colnames_xy,
                              graph=graph)