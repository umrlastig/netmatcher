# -*- coding: utf-8 -*-

import fiona

from tracklib import ENUCoords, Obs, ObsTime, Track, computeAbsCurv
from tracklib import Edge

AF_CLEABS = "#id"

def readArc(chemin):
    edges = list()
    edge_id = 1
    with fiona.open(chemin, 'r') as shapefile:
        for feature in shapefile:

            if feature.geometry["type"] != 'LineString':
                continue

            TAB_OBS = list()
            for c in feature.geometry["coordinates"]:
                x = float(c[0])
                y = float(c[1])
                z = 0.0
                point = ENUCoords(x, y, z)
                TAB_OBS.append(Obs(point, ObsTime()))

            # Au moins 2 points
            if len(TAB_OBS) < 2:
                continue

            track = Track(TAB_OBS)
            computeAbsCurv(track)

            track.tid = str(feature['properties']["ID"])

            edge = Edge(edge_id, track)
            edge_id += 1

            # Orientation
            edge.orientation = Edge.DOUBLE_SENS

            # Poids
            edge.weight = track.length()


            edges.append(edge)

    return edges


