"""Construct the nerve of a Mapper cover."""
# License: GNU AGPLv3

from functools import reduce
from itertools import combinations
from operator import iconcat

import igraph as ig
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted


class Nerve(BaseEstimator, TransformerMixin):
    """One-dimensional skeleton of the nerve of a Mapper cover, i.e. the
    Mapper graph.

    This transformer is the final step in the
    :class:`giotto.mapper.pipeline.MapperPipeline` objects created
    by :func:`giotto.mapper.make_mapper_pipeline`. It is not intended for
    direct use.

    Parameters
    ----------
    min_intersection : int, optional, default: ``1``
        The minimum size of the intersection between Mapper cover sets
        required to create an edge in the Mapper graph.

    Attributes
    ----------
    X_ : TODO: Write

    edges_ : TODO: Write

    """

    def __init__(self, min_intersection=1):
        self.min_intersection = min_intersection

    def fit(self, X, y=None):
        """Compute and store the nodes and edges of the Mapper graph,
        and return the estimator.

        Parameters
        ----------
        X : list of list of tuple
            Input data structure describing an abstract Mapper cover. Each
            sublist corresponds to a (non-empty) pullback cover set --
            equivalently, to a cover set in the filter range which has
            non-empty preimage -- and contains triples of the form ``( \
            pullback_cover_id, partial_cluster_label, indices)`` where
            ``partial_cluster_label`` is a cluster label within the pullback
            cover set identified by ``pullback_cover_id``, and ``indices``
            is the array of indices of points belonging to cluster ``( \
            pullback_cover_id, partial_cluster_label)``. In the context of a
            :class:`giotto.mapper.MapperPipeline`, this is the output of the
            clustering step.

        y : None
            There is no need for a target in a transformer, yet the pipeline
            API requires this parameter.

        Returns
        -------
        self : object

        """
        # TODO: Include a validation step for X
        self.X_ = reduce(iconcat, X, [])
        # Preprocess X by 1) flattening and 2) extending each tuple
        self.X_ = [(node_info[0], *node_info[1])
                   for node_info in zip(range(len(self.X_)), self.X_)]
        self.edges_ = list(self._generate_edges(self.X_))
        return self

    def fit_transform(self, X, y=None, **fit_params):
        """Construct a Mapper graph from an abstract Mapper cover `X`.

        Parameters
        ----------
        X : list of list of tuple
            Input data structure describing an abstract Mapper cover. Each
            sublist corresponds to a (non-empty) pullback cover set --
            equivalently, to a cover set in the filter range which has
            non-empty preimage -- and contains triples of the form ``( \
            pullback_cover_id, partial_cluster_label, indices)`` where
            ``partial_cluster_label`` is a cluster label within the pullback
            cover set identified by ``pullback_cover_id``, and ``indices``
            is the array of indices of points belonging to cluster ``( \
            pullback_cover_id, partial_cluster_label)``. In the context of a
            :class:`giotto.mapper.MapperPipeline`, this is the output of the
            clustering step.

        y : None
            There is no need for a target in a transformer, yet the pipeline
            API requires this parameter.

        Returns
        -------
        graph : :class:`igraph.Graph` object
            Mapper graph. Edges exist between two Mapper cover sets if and
            only if the size of the intersection between the two sets is no
            less than `min_intersection`.

        """
        # TODO: Include a validation step for X
        _X = reduce(iconcat, X, [])
        # Preprocess X by 1) flattening and 2) extending each tuple
        _X = [(node_info[0], *node_info[1])
              for node_info in zip(range(len(_X)), _X)]
        _edges = self._generate_edges(_X)

        # Graph construction
        graph = ig.Graph()
        graph.add_vertices([vertex[0] for vertex in _X])
        graph.add_edges([
            (edge['node_indices'][0][0], edge['node_indices'][1][0])
            for edge in _edges
        ])
        graph['node_metadata'] = dict(
            zip(['node_id', 'interval_id', 'cluster_id', 'node_elements'],
                zip(*_X)))
        return graph

    @staticmethod
    def _pairwise_intersections(min_intersection, node_pair):
        data = dict()
        node_1, node_2 = node_pair
        data['node_indices'] = tuple((node_1[0:3], node_2[0:3]))
        data['intersection'] = np.intersect1d(node_1[3], node_2[3])
        if data['intersection'].size >= min_intersection:
            yield data

    def _generate_edges(self, nodes):
        node_tuples = combinations(nodes, 2)
        for pair in node_tuples:
            for intersection in \
             self._pairwise_intersections(self.min_intersection, pair):
                yield intersection
