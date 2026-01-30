# -*- coding: utf-8 -*-


from netmatcher.process import EnsembleDeLiens, Lien, NodeNM
from netmatcher.util import selectNodes, selectEdges
from tracklib import premiereComposanteHausdorff
import sys

N1_NODES_LIENS = dict()
N2_NODES_LIENS = dict()
N1_EDGES_LIENS = dict()
N2_EDGES_LIENS = dict()

N2_NODES_RES = dict()
N1_NODES_RES = dict()


def appariementReseaux(reseau1, reseau2, param):
    '''
    Matching between two networks represented by topological maps.
    Processus largement inspiré de celui défini 
              dans la thèse de Thomas Devogèle (1997).
   
    Parameters
    ----------
    reseau1 : TYPE
        DESCRIPTION.
    reseau2 : TYPE
        DESCRIPTION.
    param : TYPE
        DESCRIPTION.

    Returns
    -------
    liens : TYPE
        DESCRIPTION.

    '''

    # Pre-matching of nodes.
    liensPreAppNN = preAppariementNoeudNoeud(reseau1, reseau2, param)

    # Pre-matching of edges
    if len(liensPreAppNN) > 0:
        # liensPreAppAA sur les noeuds. Preappariement des arcs entre eux
        # (basé principalement sur Hausdorf).
        liensPreAppAA = preAppariementArcArc(reseau1, reseau2, param)
    else:
        # Nothing to do if there is no node.
        # Il est inutile de pre-appariéer les arcs si rien n'a été trouvé
        liensPreAppAA = EnsembleDeLiens("Edges Prematching")

    # Matching each node of reseau1 independantly with nodes of reseau2
    # Appariement de chaque noeud de la BDref / reseau1
    # (indépendamment les uns des autres)
    liensAppNoeuds = appariementNoeuds(reseau1,reseau2, liensPreAppNN, liensPreAppAA, param)

    liens = None
    return liens



def preAppariementNoeudNoeud(network1, network2, param):
    '''
    Nodes Prematching using euclidian distance as proposed in [Devogèle 97].
   
    On crée des liens 1-n (n candidats noeuds de BDcomp pour chaque noeud de BDref).
    NB1: On ne traite pas les noeuds isolés.
    
    @param network less detailed NetworkNM 
    @param network more detailed NetworkNM 
    @param param matching paramters
    @return resulting set of links between networks

    '''
    print ('.... Pré-appariement des noeuds')

    liens = EnsembleDeLiens("Nodes prematching")

    nbCandidats = 0
    nbRef = 0

    for idnode1 in network1.getNodesId():

        # On ne tient pas compte des noeuds isolés
        if len(network1.getPrevEdges(idnode1)) == 0 and len(network1.getNextEdges(idnode1)) == 0:
            continue

        nbRef += 1

        # Détermination des noeuds comp dans le rayon de recherche
        nr = network1.getNode(idnode1)
        candidates = selectNodes(network2, nr, param.getDistanceNoeudsMax())
        if len(candidates) > 0:
            lien = Lien()
            lien.addNoeuds1(nr)
            N1_NODES_LIENS[idnode1] = lien
            nbCandidats += len(candidates)
            for noeudComp in candidates:
                lien.addNoeuds2(noeudComp)
                N2_NODES_LIENS[noeudComp.id] = lien
            liens.addLien(lien)

    print ("     Assessment : ", nbCandidats, "Candidate Comp Nodes for ",
           nbRef, "Ref nodes to process")

    return liens




def preAppariementArcArc(network1, network2, param):
    '''
    Edges prematching using Haussdorff half distance.
    * <p>
    * Préappariement entre arcs basé sur la "demi-distance de Hausdorff" (on ne
    * prend en compte que la composante de réseau 2 vers réseau 1).
    * 
    * Pour chaque arc du reseau 2, on garde les arcs du reseau 1 qui sont à la fois : 
    * 1/ à moins distanceMax de l'arc comp 
    * 2/ à moins de D + distanceMin de l'arc comp, 
    *    D étant la distance entre l'arc ref le plus proche de arc comp
    * 
    * NB: ce pré-appariement est différent de ce qui est proposé dans [Devogèle 97], 
    *     pour minimiser la sensibilité aux seuils.
    * 
    * On crée des liens 1-n: (1 arc de comp) - (n arcs de ref). Un arc de ref
    * peut être alors concerné par plusieurs liens différents. Au total on a donc
    * des relations n-m codées sous la forme de n relations 1-m.

    Parameters
    ----------
    reseau1 : NetworkNM
        network 1.
    reseau2 : NetworkNM
        network 2.
    param : ParameterNM
        matching parameters.

    Returns
    -------
    resulting set of links.

    '''

    print ('.... Pré-appariement des arcs')
    liens = EnsembleDeLiens("Edges Prematching")

    nbCandidats = 0


    for arcComp in network2:

        # On recherche les arcs dans l'entourage proche, grosso modo
        arcsProches = selectEdges(network1, arcComp.geom, param.getDistanceArcsMax())
        n = len(arcsProches)
        if n > 19:
            print (n, arcComp.geom.tid)
        if len(arcsProches) <= 0:
            continue

        # On calcule leur distance à arccomp et on recherche le plus proche
        distances = list()

        resampled = arcComp.geom.copy()
        resampled.resample(param.distanceArcsMax)

        arcRef = arcsProches[0]
        dmin = premiereComposanteHausdorff(resampled, arcRef.geom)
        if dmin > param.distanceArcsMax:
            dmin = sys.float_info.max
        distances.append(dmin)

        for i in range(1, len(arcsProches)):
            arcRef = arcsProches[i]
            d = premiereComposanteHausdorff(resampled, arcRef.geom)
            if d > param.distanceArcsMax:
                d = sys.float_info.max
            distances.append(d);
            if d < dmin:
                dmin = d

        # On garde tous ceux assez proches
        dmax = min(dmin + param.distanceArcsMin, param.distanceArcsMax)
        candidats = list()
        for i in range(len(arcsProches)):
            arc = arcsProches[i]
            distance = distances[i]
            if distance < dmax:
                candidats.append(arc)

        # Si pas de candidat pour l'arccomp, on s'arrête là
        if len(candidats) <= 0:
            continue

        # Si il y a des candidats: on construit le lien de pré-appariement
        lien = Lien()
        N2_EDGES_LIENS[arcComp.id] = lien
        lien.addArcs2(arcComp)
        nbCandidats += len(candidats)
        
        for arcRef in candidats:
            lien.addArcs1(arcRef)
            N1_EDGES_LIENS[arcRef.id] = lien
        liens.addLien(lien)


    print ("     Assessment : ", nbCandidats, "Candidate Comp Edges for ",
           network1.size(), "Ref edges to process")

    return liens



def appariementNoeuds(network1, network2, liensPreAppNN, liensPreAppAA, param):
    '''
    Node matching of network 1 with network 2 as proposed in [Devogèle 97].
    Matches are evaluated with a mark of (0, 0.5, or 1).
   
    Appariement des Noeuds du reseau 1 avec les arcs et noeuds du reseau 1,
    comme proposé dans [Devogèle 97] + modif au filtrage Seb On crée les liens
    qui vont bien si le noeud est apparié. Une évaluation de l'appariement est
    stockée sur les liens (note de 0, 0.5 ou 1). Une explication plus détaillée
    du résultat est stockée sur les noeuds ref et comp.
    
    '''
    print ('.... Nodes Matching')

    liens = EnsembleDeLiens("Nodes Matching")

    nbSansHomologue = 0
    nbNonTraite = 0
    nbPlusieursNoeudsComplets = 0
    nbPlusieursGroupesComplets = 0
    nbNoeudNoeud = 0
    nbNoeudGroupe = 0
    nbNoeudGroupeIncertain = 0
    nbNoeudNoeudIncertain = 0

    # groupesComp = network2.getPopGroupes()

    # On initialise le resultat à "non apparié" pour les noeuds comp
    for key in network2.getIndexNodes():
        N2_NODES_RES[key] = NodeNM()


    # On traite chaque noeud ref, un par un
    for idnode1 in network1.getNodesId():
        noeudRef = network1.getNode(idnode1)

        # pour détecter les cas non traités
        N1_NODES_RES[idnode1] = "Bug: not available"

        # On ne traite pas les noeuds isolés
        if len(network1.getNextEdges(idnode1)) == 0 and len(network1.getPrevEdges(idnode1)) == 0:
            N1_NODES_RES[idnode1] = "Unhandled isolated node"
            nbNonTraite += 1
            continue

        # Noeud ref qui n'a aucun noeud comp candidat dans le pré-appariement
        if idnode1 not in N1_NODES_LIENS or not isinstance(N1_NODES_LIENS[idnode1], Lien):
            # print (len(N1_NODES_LIENS[idnode1].getNoeuds2()), len(liensPreAppNN))
            N1_NODES_RES[idnode1] = "No candidate for matching"
            nbSansHomologue += 1
            continue


        # Noeud ref qui a un ou plusieurs candidats (réunis dans un seul lien par construction).
        # On qualifie des noeuds comp candidats en comparant les entrants/sortants.
        # Un noeud comp est dit, par rapport au noeud ref :
        # - complet si on trouve une correspondance entre tous les incidents des noeuds ref et comp,
        # - incomplet si on trouve une correspondance entre certains incidents
        # - impossible si on ne trouve aucune correspondance
        noeudsCompCandidats = N1_NODES_LIENS[idnode1].getNoeuds2()
        complets = list()
        incomplets = list()
        for noeudComp in noeudsCompCandidats:
            correspondance = correspCommunicants(noeudRef, noeudComp, liensPreAppAA)
            '''
            if correspondance == 1:
                    # complets.add(noeudComp)
                if correspondance == 0:
                    # incomplets.add(noeudComp)
            '''










    # =========================================================================
    # =========================================================================
    print ("     Nodes assessment:")
    # -------------------------------------------------------------------------
    print ("         Matches judges Correct:")
    print ("            ", nbNoeudNoeud, "Nodes of network 1 matched with a single node")
    print ("            ", nbNoeudGroupe, "Nodes of network 1 matched with a group")
    # -------------------------------------------------------------------------
    print ("         Matches judged uncertain:")
    print ("            ", nbNoeudNoeudIncertain, "Nodes of network 1 matched with a single incomplete node")
    print ("            ", nbPlusieursNoeudsComplets, "Nodes of network 1 matched with several nodes")
    print ("            ", nbNoeudGroupeIncertain, "Nodes of network 1 matched with a single incomplete group")
    # -------------------------------------------------------------------------
    print ("         Matches judges incoherent:")
    print ("            ", nbSansHomologue, "Nodes of network 1 without match")
    print ("            ", nbPlusieursGroupesComplets, "Nodes of network 1 with several homologous groups")
    # -------------------------------------------------------------------------
    print ("         Unprocessed nodes:")
    print ("            ", nbNonTraite, "Isolated nodes of network 1")
    # -------------------------------------------------------------------------




def correspCommunicants(noeud1, noeud2, liensPreAppAA):
    '''
    '''

    return None


