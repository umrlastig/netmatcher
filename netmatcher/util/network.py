# -*- coding: utf-8 -*-


from tracklib import Network, Node
from tracklib import compare, MODE_COMPARISON_HAUSDORFF
import tracklib as tkl
import sys

tkl.NetworkReader.counter = 1


def createNetwork(collection, tolerance):
    network = tkl.Network()
    cptNode = 0

    for track in collection:
        tkl.computeAbsCurv(track)

        edge_id = tkl.NetworkReader.counter
        tkl.NetworkReader.counter = tkl.NetworkReader.counter + 1
        edge = tkl.Edge(edge_id, track)
        edge.orientation = tkl.Edge.DOUBLE_SENS
        edge.weight = track.length()

        # On cherche si les noeuds n'existent pas déjà et si c'est le cas
        #   on change aussi la géométrie des premiers et derniers noeuds

        # Source node
        p1 = track.getFirstObs().position
        candidates1 = tkl.selectNodes(network, tkl.Node(-1, p1), tolerance)
        if len(candidates1) == 1:
            noeudIni = candidates1[0]
            edge.geom.setObs(0, tkl.Obs(noeudIni.coord, tkl.ObsTime()))
        elif len(candidates1) > 1:
            # plusieurs, on prend le plus proche
            d = sys.float_info.max
            for c in candidates1:
                if c.coord.distance2DTo(p1) <= d:
                    noeudIni = c
                    edge.geom.setObs(0, tkl.Obs(c.coord, tkl.ObsTime()))
                    d = c.coord.distance2DTo(p1)
        else:
            noeudIni = tkl.Node(cptNode, p1)
            cptNode += 1


        # Target node
        p2 = track.getLastObs().position
        candidates2 = tkl.selectNodes(network, tkl.Node(-2, p2), tolerance)
        if noeudIni in candidates2:
            candidates2.remove(noeudIni)

        if len(candidates2) == 1:
            noeudFin = candidates2[0]
            edge.geom.setObs(edge.geom.size()-1, tkl.Obs(noeudFin.coord, tkl.ObsTime()))
        elif len(candidates2) > 1:
            d = sys.float_info.max
            for c in candidates2:
                if c.coord.distance2DTo(p2) < d:
                    noeudFin = c
                    edge.geom.setObs(edge.geom.size()-1, tkl.Obs(c.coord, tkl.ObsTime()))
                    d = c.coord.distance2DTo(p2)
        else:
            noeudFin = tkl.Node(cptNode, p2)
            cptNode += 1


        #
        existant = False
        for edge2 in network:
            if edge.id == edge2.id:
                continue
            track2 = edge2.geom
            track1 = edge.geom
            mode=tkl.MODE_COMPARISON_POINTWISE
            p=1
            dim=2
            d = tkl.compare(track1, track2, mode, p, dim)
            if d < 0.1:
                existant = True

        if not existant:
            network.addEdge(edge, noeudIni, noeudFin)

    return network


def filtreNoeudSimple(network):
    '''
    Filtre des noeuds simples
    #  c'est-à-dire avec seulement deux arcs incidents,
    #           si ils ont des orientations compatibles.
    # Ces noeuds sont enlevés et un seul arc est créé à la place
    # des deux arcs incidents.
    '''

    noeudsElimines = []

    for idnode in network.getIndexNodes():
        node = network.NODES[idnode]
        pt = node.coord

        if idnode not in network.NBGR_EDGES:
            continue
        nb = len(network.getIncidentEdges(idnode))
        if nb != 2:
            continue

        arc1 = network.EDGES[network.NBGR_EDGES[idnode][0]]
        n1i = arc1.source.id
        n1f = arc1.target.id
        arc2 = network.EDGES[network.NBGR_EDGES[idnode][1]]
        n2i = arc2.source.id
        n2f = arc2.target.id


        # On construit la nouvelle trace, attention au sens de la géométrie
        # quel noeud pour ni et nf ?
        ni = None
        nf = None
        nm = None

        if n1f == n2i:
            # print ('     sens : ', arc1.source.id, arc1.target.id, arc2.target.id)
            track = arc1.geom + arc2.geom
            ni = arc1.source
            nf = arc2.target
            nm = arc1.target
            if nm.id != arc2.source.id:
                print ('probleme 1')
        elif n1f == n2f:
            track = arc1.geom + arc2.geom.reverse()
            ni = arc1.source
            nf = arc2.source
            nm = arc1.target
            if nm.id != arc2.target.id:
                print ('probleme 2')
        elif n1i == n2i:
            track = arc1.geom.reverse() + arc2.geom
            ni = arc1.target
            nf = arc2.target
            nm = arc1.source
            if nm.id != arc2.source.id:
                print ('probleme 3')
        elif n1i == n2f:
            track = arc1.geom.reverse() + arc2.geom.reverse()
            ni = arc1.target
            nf = arc2.source
            nm = arc1.source
            if nm.id != arc2.target.id:
                print ('probleme 4')


        # Nouvel arc
        edge_id = tkl.NetworkReader.counter
        tkl.NetworkReader.counter = tkl.NetworkReader.counter + 1

        edgefusion = tkl.Edge(edge_id, track)
        edgefusion.orientation = tkl.Edge.DOUBLE_SENS
        edgefusion.weight = track.length()
        #if str(idnode) == '2365':
        #    print ('     nouvel arc : ', edge_id, ni.id, nf.id)
        #    print ('     anciens arcs : ', arc1.id, arc2.id)
        #    print ('     arc du milieu : ', nm.id)

        if ni is None or nf is None:
            print ('NULL')

        # on crée
        try :
            network.addEdge(edgefusion, ni, nf)
        except Exception as e:
            print (n1i, n1f, n2i, n2f)
            print (e)


        # on supprime les incidences du noeud du milieu
        del network.PREV_EDGES[nm.id]
        del network.NEXT_EDGES[nm.id]
        del network.NBGR_EDGES[nm.id]

        network.NEXT_EDGES[ni.id].remove(arc1.id)
        network.NBGR_EDGES[ni.id].remove(arc1.id)
        network.NEXT_NODES[ni.id].remove(nm.id)
        network.NBGR_NODES[ni.id].remove(nm.id)

        network.PREV_EDGES[nf.id].remove(arc2.id)
        network.NBGR_EDGES[nf.id].remove(arc2.id)
        network.PREV_NODES[nf.id].remove(nm.id)
        network.NBGR_NODES[nf.id].remove(nm.id)

        # On supprime le noeud du milieu
        noeudsElimines.append(idnode)
        # network.removeNode(node)

        network.removeEdge(arc2)
        network.removeEdge(arc1)


    if len(noeudsElimines) > 0:
        # print (NoeudsASupprimer)
        for nid in noeudsElimines:
            node = network.NODES[nid]
            network.removeNode(node)



def deleteSmallEdge(network, threshold):
    '''
       Suppression des petits arcs et qui n'ont qu'une seule incidence
    '''
    for eid in network.getIndexEdges():
        edge = network.EDGES[eid]
        ni = edge.source
        nf = edge.target
        if edge.geom.length() < threshold and (len(network.getIncidentEdges(ni.id)) <= 1
                        or len(network.getIncidentEdges(nf.id)) <= 1):

            if len(network.getIncidentEdges(ni.id)) <= 1:
                # print ('suppression à faire ', edge.id, ni.id)
                # on supprime le noeud
                network.NEXT_NODES[nf.id].remove(ni.id)
                network.NEXT_EDGES[nf.id].remove(edge.id)
                network.NBGR_NODES[nf.id].remove(ni.id)
                network.NBGR_EDGES[nf.id].remove(edge.id)

                if ni.id in network.getIndexNodes():
                    network.removeNode(ni)
                else:
                    print ('------', ni.id)

            if len(network.getIncidentEdges(nf.id)) <= 1:
                # print ('suppression à faire ', edge.id, nf.id)
                # on supprime le noeud
                network.NEXT_NODES[ni.id].remove(nf.id)
                network.NEXT_EDGES[ni.id].remove(edge.id)
                network.NBGR_NODES[ni.id].remove(nf.id)
                network.NBGR_EDGES[ni.id].remove(edge.id)

                network.removeNode(nf)

            network.removeEdge(edge)



class NetworkNM():

    @staticmethod
    def filtreNoeudsSimples(network):
        nb = len(network.NBGR_EDGES[node])        
        pass

    @staticmethod
    def filtreDoublons(network, tolerance):
        '''
        /**
        * Filtrage des noeuds doublons (plusieurs noeuds localisés au même endroit).
        * <ul>
        * <li>NB: si cela n'avait pas été fait avant, la population des noeuds est
        * indexée dans cette méthode (dallage, paramètre = 20).
        * <li>Cette méthode gère les conséquences sur la topologie, si celle-ci a été
        * instanciée auparavant.
        * <li>Cette méthode gère aussi les conséquences sur les correspondants (un
        * noeud gardé a pour correspondants tous les correspondants des doublons).
        * </ul>
        * @param tolerance Le paramètre tolérance spécifie la distance maximale pour
        *          considérer deux noeuds positionnés au même endroit.
        */
        '''
        print ("         Double nodes filtering")

        aJeter = list()
        selection = None



        '''
        
        for (Noeud noeud : this.getPopNoeuds()) {
          if (aJeter.contains(noeud)) {
            continue;
          }
          selection = this.getPopNoeuds().select(noeud.getCoord(), tolerance);
          selection.remove(noeud);
          for (Noeud doublon : selection) {
            // on a trouvé un doublon à jeter
            // on gère les conséquences sur la topologie et les
            // correspondants
            aJeter.add(doublon);
            noeud.addAllCorrespondants(doublon.getCorrespondants());
            for (Arc a : new ArrayList<Arc>(doublon.getEntrants())) {
              noeud.addEntrant(a);
            }
            for (Arc a : new ArrayList<Arc>(doublon.getSortants())) {
              noeud.addSortant(a);
            }
          }
        }
        this.getPopNoeuds().removeAll(aJeter);
        '''

    @staticmethod
    def creeTopologieArcsNoeuds(edges, cptNode, tolerance):
        '''
        Instancie la topologie de réseau d'une Carte Topo, en se basant sur la
        géométrie 2D des arcs et des noeuds. Autrement dit: crée les relations
        "noeud initial" et "noeud final" d'un arc.
        
        - ATTENTION: cette méthode ne rajoute pas de noeuds. Si un arc
          n'a pas de noeud localisé à son extrémité, il n'aura pas de noeud initial
          (ou final).
        - DE PLUS si plusieurs noeuds sont trop proches (cf. param tolérance), 
          alors un des noeuds est choisi au hasard pour la relation arc/noeud, 
          ce qui n'est pas correct.
        - IL EST DONC CONSEILLE DE FILTRER LES DOUBLONS AVANT SI NECESSAIRE.
        - NB: si cela n'avait pas été fait avant, la population des noeuds est
          indexée dans cette méthode (dallage, paramètre = 20).
        
        @param tolerance Le paramètre "tolerance" spécifie la distance maximale
               acceptée entre la position d'un noeud et la position d'une
               extrémité de ligne, pour considérer ce noeud comme extrémité (la
               tolérance peut être nulle).
        '''

        print ("         Construction of the topology between edges and nodes")

        network = Network()

        # Crée un nouveau noeud à l'extrémité de chaque arc si il n'y en a pas.
        # La topologie arcs/noeuds est instanciée au passage
        for edge in edges:

            if edge.geom.size() < 2:
                # warning: Edge has only 1 or 0 point and was ignored
                print ('warning: Edge has only 1 or 0 point and was ignored')
                continue

            # Source node
            idNoeudIni = str(cptNode)
            p1 = edge.geom.getFirstObs().position
            candidates = selectNodes(network, Node("0", p1), 0.5)
            if len(candidates) > 0:
                c = candidates[0]
                idNoeudIni = c.id
            else:
                cptNode += 1
            noeudIni = Node(idNoeudIni, p1)

            # Target node
            idNoeudFin = str(cptNode)
            p2 = edge.geom.getLastObs().position
            candidates = selectNodes(network, Node("0", p2), 0.5)
            if len(candidates) > 0:
                c = candidates[0]
                idNoeudFin = c.id
            else:
                cptNode += 1
            noeudFin = Node(idNoeudFin, p2)

            network.addEdge(edge, noeudIni, noeudFin)

        return (network, cptNode)



def selectNodes(network, node, distance):
    """Selection des autres noeuds dans le cercle dont node.coord est le centre,
    de rayon distance

    :param node: le centre du cercle de recherche.
    :param distance: le rayon du cercle de recherche.

    :return: tableau de NODES liste des noeuds dans le cercle
    """
    NODES = []

    if network.spatial_index is None:
        for key in network.getIndexNodes():
            n = network.NODES[key]
            if n.coord.distance2DTo(node.coord) <= distance:
                NODES.append(n)
    else:
        print ('INDEX !!!!!!')
        vicinity_edges = network.spatial_index.neighborhood(node.coord, unit=1)
        for e in vicinity_edges:
            source = network.EDGES[network.getEdgeId(e)].source
            target = network.EDGES[network.getEdgeId(e)].target
            if source.coord.distance2DTo(node.coord) <= distance:
                NODES.append(source)
            if target.coord.distance2DTo(node.coord) <= distance:
                NODES.append(target)

    return NODES


def selectEdges(network, line, distance):
    '''
    liste des arcs de la collection dans un voisinnage de tolerance de line

    Parameters
    ----------
    self.nodes : TYPE
        DESCRIPTION.
    edge.startPoint() : TYPE
        DESCRIPTION.
    tolerance : TYPE
        DESCRIPTION.

    Returns
    -------
    list : liste de noeuds

    '''

    selections = list()

    if network.spatial_index is None:
        for edge in network:
            track = edge.geom
            if compare(track, line, mode=MODE_COMPARISON_HAUSDORFF, verbose=False) <= distance:
                selections.append(edge)
    else:
        print ('INDEX !!!!!!')
        network.spatial_index.neighborhood(line, unit=1)

    return selections




