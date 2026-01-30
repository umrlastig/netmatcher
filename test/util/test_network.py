# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import sys
import tracklib as tkl
import unittest
from netmatcher import (createNetwork, filtreNoeudSimple)



class TestUtilNetwork(unittest.TestCase):
    

    
    def setUp (self):
        self.collection = tkl.TrackCollection()
        wkt1 = 'LineString (949464.54181289207190275 6511189.01651289127767086, 949465.41049999999813735 6511188.81468277052044868)'
        wkt2 = 'LineString (949465.41049999999813735 6511187.94359373487532139, 949465.41049999999813735 6511188.81468277052044868)'
        wkt3 = 'LineString (949465.62881248281337321 6511189.69476869702339172, 949465.41049999999813735 6511188.81468277052044868)'
        wkt4 = 'LineString (949465.62881248281337321 6511189.69476869702339172, 949468.1601792813744396 6511191.25851298123598099)'
        wkt5 = 'LineString (949468.37692472361959517 6511192.10310463793575764, 949468.1601792813744396 6511191.25851298123598099)'
        wkt6 = 'LineString (949468.37692472361959517 6511192.10310463793575764, 949466.86878196173347533 6511194.67706254497170448)'
        wkt7 = 'LineString (949466.86878196173347533 6511194.67706254497170448, 949467.20845044264569879 6511196.06949897296726704)'
        wkt8 = 'LineString (949465.03866808395832777 6511196.55419210344552994, 949467.20845044264569879 6511196.06949897296726704)'
        wkt9 = 'LineString (949467.20845044264569879 6511196.06949897296726704, 949467.61479663848876953 6511196.07794086635112762)'
        wkt10 = 'LineString (949467.61479663848876953 6511196.07794086635112762, 949469.45157357701100409 6511197.91671759262681007)'
        wkt11 = 'LineString (949469.45157357701100409 6511197.91671759262681007, 949469.94407232687808573 6511199.69164014235138893)'

        WKTs = [wkt1, wkt2, wkt3, wkt4, wkt5, wkt6, wkt7, wkt8, wkt9, wkt10, wkt11]
        for wkt in WKTs:
            track = tkl.TrackReader().parseWkt(wkt)
            if track.size() < 2 :
                continue
            self.collection.addTrack(track)

    
    def testCreation(self):
        
        tolerance = 0.5
        network = createNetwork(self.collection, tolerance)

        network.plot()
        for eid in network.getIndexEdges():
            edge = network.EDGES[eid]
            x1 = edge.geom.getFirstObs().position.getX()
            y1 = edge.geom.getFirstObs().position.getY()
            x2 = edge.geom.getLastObs().position.getX()
            y2 = edge.geom.getLastObs().position.getY()
            plt.text((x1+x2)/2, (y1+y2)/2, str(eid), fontsize=14)
        plt.show()

        self.assertEqual(len(network.EDGES), 11, "Number of edges")
        self.assertEqual(len(network.NODES), 12, "Number of nodes")
        self.assertLessEqual(abs(18 - network.totalLength()), 0.01, "Total length of all edges")


    def testFiltre(self):

        tolerance = 0.5
        network = createNetwork(self.collection, tolerance)
        filtreNoeudSimple(network)

        '''

        network.plot()
        for eid in network.getIndexEdges():
            edge = network.EDGES[eid]
            x1 = edge.geom.getFirstObs().position.getX()
            y1 = edge.geom.getFirstObs().position.getY()
            x2 = edge.geom.getLastObs().position.getX()
            y2 = edge.geom.getLastObs().position.getY()
            plt.text((x1+x2)/2, (y1+y2)/2, str(eid), fontsize=14)
        plt.show()

        print ('Number of edges = ', len(network.EDGES))
        print ('Number of nodes = ', len(network.NODES))
        print ('Total length of all edges = ', network.totalLength())
        '''



if __name__ == '__main__':
    suite = unittest.TestSuite()

    suite.addTest(TestUtilNetwork("testCreation"))
    suite.addTest(TestUtilNetwork("testFiltre"))

    runner = unittest.TextTestRunner()
    runner.run(suite)
