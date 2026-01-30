# -*- coding: utf-8 -*-


from netmatcher.util import NetworkNM
from netmatcher.process import appariementReseaux
from netmatcher.process import N1_NODES_LIENS, N2_NODES_LIENS
from netmatcher.process import N1_EDGES_LIENS, N2_EDGES_LIENS
from netmatcher.process import N2_NODES_RES


N1_CORRESPOND = dict()
N2_CORRESPOND = dict()

'''

Lancement de l'appariement de réseaux sur des objets Géographiques: 
    1- Transformation des données initales en deux graphes, 
       en fonction des paramètres d'import, 
    2- Lancement du calcul d'appariement générique sur les deux réseaux, 
    3- Analyse et export des résultats éventuellement.
@return             L'ensemble des liens en sortie (de la classe EnsembleDeLiens).
@param paramApp     Les paramètres de l'appariement (seuls de distance,
                    préparation topologique des données...)
@param cartesTopo   Liste en entrée/sortie qui permet de Récupèrer en sortie
                    les graphes intermédiaires créés pendant le calcul (de type
                    Reseau_App, spécialisation de CarteTopo). - Si on veut Récupèrer
                    les graphes : passer une liste vide - new ArrayList() - mais non
                    nulle. Elle contient alors en sortie 2 éléments : dans l'ordre les
                    cartes topo de référence et comparaison. Elle peut contenir un
                    3eme élément: le graphe ref recalé sur comp si cela est demandé
                    dans les paramètres. - Si on ne veut rien Récupèrer : passer Null
             
'''


# EnsembleDeLiens appariementDeJeuxGeo(ParametresApp paramApp, List<ReseauApp> cartesTopo)
def appariementDeJeuxGeo(param):
    print ('.... MatchingStart')

    cptNode = 1

    # construction des cartes topos
    (network1, cptNode) = importData(param, True, cptNode)
    (network2, cptNode) = importData(param, False, cptNode)

    # NB: l'ordre dans lequel les projections sont faites n'est pas neutre
    # reseauRef.instancieAttributsNuls(paramApp.distanceNoeudsMax);
    # reseauComp.initialisePoids();


    liens = appariementReseaux(network1, network2, param)
    return (network1, network2, liens)




def importData(param, is1, cptNode):

    # Network.setEdges
    if is1:
        print ('     reference network (net1)')
        edges = param.getPopulationsArcs1()
    else:
        print ('     comparison network (net2)')
        edges = param.getPopulationsArcs2()

    # Construction of the topology between edges and nodes
    (network, cptNode) = NetworkNM.creeTopologieArcsNoeuds(edges, cptNode, 0.5)
    #      reseau.creeNoeudsManquants(0.1)
    # NetworkNM.filtreDoublons(network, 0.1)
    #      reseau.filtreArcsDoublons();
    #      // Fin Ajout
    #      reseau.rendPlanaire(0.1);
    #      reseau.filtreDoublons(0.1);

    print ('          nb edges = ', network.getNumberOfEdges())
    print ('          nb nodes = ', network.getNumberOfNodes())

    return network, cptNode




















