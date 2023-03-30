# pySCY_To_CSV
# Convert the file SCY schneider Unity in CSV for HMI proface & HMI Schneider Vijeo

import os
import re
import xml.etree.ElementTree as xml
import lxml
from lxml import etree



def FilePrintXml(Parent, Name, Type, Adresse):

    if len(Name) > 32 :
        return


    # Element type variable
    v1 = xml.Element("Variable")
    v1.set("name", Name)
    v1.set("type", Type)
    folder.append(v1)


    sub1 = xml.SubElement(v1, "Source")
    sub1.text = "External"

    sub2 = xml.SubElement(v1, "Sharing")
    sub2.text = "None"

    sub3 = xml.SubElement(v1, "ScanGroup")
    sub3.text = "EquipementModbus01"

    sub4 = xml.SubElement(v1, "DeviceAddress")
    sub4.text = Adresse

    sub5 = xml.SubElement(v1, "LogUserOperations")
    sub5.text = "Disabled"



def FilePrintLine(Text):
    global CptVariable2
    print(Text)
    OutputFile.write(Text + "\n")
    CptVariable2 += 1


# Fonction qui retourne la valeur numéric de l'adresse mémoire
def AdressNumber(Adr):
    return int(''.join(list(filter(str.isdigit, Adr))))


# Fonction qui dépli le DTT

def resolveDTT(root, type, nameParent, name, adresseIn, comment, attributExtractBit) -> object:
    adresse = adresseIn

    global CptBit
    global CptVariable
    global listName
    global adresseExctractBit

    # Variable de type MOT (Word, INT, UINT)
    if type in ["WORD", "DWORD", "INT", "DINT", "UINT", "UDINT"]:

        if CptBit != 0:
            adresse = adresse + 1

        nameVar = (nameParent + delimiterVariable + name)
        if len(nameParent + delimiterVariable + name) > 32:
            listName.append(nameVar)
        else:
            FilePrintLine(nameVar + delimiter + wordName + delimiter + "%MW" + str(adresse) + delimiter + comment + delimiter)

            if type == "WORD":
                typeVijeo = "INT"
            elif type == "DWORD" :
                typeVijeo = "DINT"
            else :
                typeVijeo = type

            FilePrintXml(nameParent,nameVar, str(typeVijeo), "%MW"+str(adresse))

        # Increment de l'adresse mémoire
        adresseExctractBit = adresse
        CptBit = 0
        #CptVariable += 1
        if type in ["DWORD", "DINT", "UDINT"]:
            adresse = adresse + 2
        if type in ["WORD", "INT", "UINT"]:
            adresse = adresse + 1

    # Variable de type Booléenne (BOOL)
    elif type in ["BOOL"]:

        nameVar = (nameParent + delimiterVariable + name)

        if len(nameParent + delimiterVariable + name) > 32:
            listName.append(nameVar)

        if attributExtractBit is not None:
            if len(nameParent + delimiterVariable + name) <= 32:
                FilePrintLine(nameVar + delimiter + bitName + delimiter + "%MW" + str(adresseExctractBit) + ":X" + str(
                     attributExtractBit).zfill(2) + delimiter + comment + delimiter)
                FilePrintXml(nameParent,nameVar, str(type), "%MW" + str(adresseExctractBit)+ ":X" + str(attributExtractBit).zfill(2))
        else:
            if len(nameParent + delimiterVariable + name) <= 32:
                FilePrintLine(nameVar + delimiter + bitName + delimiter + "%MW" + str(adresse) + ":X" + str(CptBit).zfill(
                       2) + delimiter + comment + delimiter)
                FilePrintXml(nameParent,nameVar, str(type), "%MW" + str(adresseExctractBit) + ":X" + str(CptBit).zfill(2))

            # Incrément du bit
            CptBit = CptBit + 1

            # Si dépassement increment de l'addresse et mise à zero du bit
            if CptBit > 15:
                CptBit = 0
                adresse = adresse + 1
           #CptVariable += 1

    # Variable de type STRING
    elif re.search(r"string\[(?P<longueur>\d*)]", type) is not None:

        # Récupération de la longueur du string
        arrayLong = re.search(r"string\[(?P<longueur>\d*)]", type)
        long = int(arrayLong.group('longueur'))
        if len(nameParent + delimiterVariable + name) <= 32:
            FilePrintLine(nameParent + delimiterVariable + name + str(
              long).zfill(2) + delimiter + wordName + delimiter + "%MW" + str(adresse) + delimiter + comment)

            FilePrintXml(nameParent,nameParent + delimiterVariable + name + str(long).zfill(2), wordName, "%MW" + str(adresse))

        # Incément de l'adresse de la longueur du string
        adresse += int(long / 2)
        #CptVariable += 1

    # Variable de type tableau (ARRAY[1..6] OF WORD
    elif re.search(r"ARRAY\[(?P<indexDepart>\d*)\.\.(?P<indexFin>\d*)] OF (?P<data>\w*)", type) is not None:

        # Récupération de la longueur du tableau et du type de donnée du tableau
        arrayType = re.search(r"ARRAY\[(?P<indexDepart>\d*)\.\.(?P<indexFin>\d*)] OF (?P<data>\w*)", type)
        deb = int(arrayType.group('indexDepart'))
        fin = int(arrayType.group('indexFin'))
        childType = arrayType.group('data')

        # itération du tableau de donnée
        for i in range(deb, fin + 1):
            if nameParent == delimiterVariable:
                nameParent = ""

            # appel de la fonction recursive
            adresse = resolveDTT(root, childType, nameParent, name + str(i).zfill(2), adresse, comment, None)

    else:
        # Itération des variables du DTT
        child: object

        for child in root.findall(".//DDTSource[@DDTName='" + type + "']/structure/variables"):

            # Récupération du type de DDT
            TypeName = child.get("typeName")
            Name = child.get("name")

            # Recupere le commentaire de la variable
            cmt = ""
            comment = child.find("comment")
            if comment is not None:
                cmt = comment.text

            attributExtractBit = None
            element: object
            for element in child.iterfind('attribute'):
                if element.get('name') == 'ExtractBit':
                    attributExtractBit = element.get('value')

            # appel de la fonction recursive
            if nameParent == "":
                delimiterVariable2 = ""
            else:
                delimiterVariable2 = delimiterVariable

            adresse = resolveDTT(root, TypeName, nameParent + delimiterVariable2 + name, Name, adresse, cmt,
                                 attributExtractBit)

    return adresse

import os.path

# Debut du programme
if __name__ == '__main__':

    # Parametre de sorties
    delimiter = ","
    delimiterVariable = "_"
    wordName = "INT"
    bitName = "BOOL"
    CptBit = 0
    CptVariable = 0
    CptVariable2 = 0
    listName = []


    # Fichier XML à parser
    path = "InputFile.XSY"

    OutputFile = open("OutGPpro.csv", "w")
    print("_____________________________________________________________________________________________ ")
    print("|                                                                                            |")
    print("|                      XSY TO CSV / XML (For Proface & Schneider)                            |")
    print("|                                                                                            |")
    print("| Ce programme permet de convertir un fichier XSY généré par Unity Schneider                 |")
    print("| au format CSV et XML afin d'importer la liste de variables dans GP-PRO Proface             |")
    print("| et Vijeo designer Schneider.                                                               |")
    print("|                                                                                            |")
    print("| -Le fichier XCY doit ce trouver dans le même répertoire que ce programmme                  |")
    print("| -Le fichier XCY doit se nommer InputFile.XSY                                               |")
    print("| -Le nom des variables de sortie supérieur à 32 caractères ne sont par pris en charge par   |")
    print("|  Vijeo designer et GP-pro.                                                                 |")
    print("| -Ce programme prend en charge uniquement les variables aillant une adresse %MW en          |")
    print("|  adresse de départ.                                                                        |")
    print("|____________________________________________________________________________________________|")
    os.system("pause")

    if  not(os.path.exists(path)) :
        print("Le fichier XSY doit avoir le nom : InputFile.XSY")
        os.system("pause")
        exit()

    tree = lxml.etree.parse(path)
    root = tree.getroot()

    #Fichier Xml Schneider de sortie
    RootXml = xml.Element("VariableData")
    RootXml.set("version", "5.1")

    # Iteration des différentes variables
    for VARIABLE in root.xpath("/VariablesExchangeFile/dataBlock/variables"):

        # Traitement uniquement des variables avec un adresse mémoire localisée
        if VARIABLE.get("topologicalAddress") and '%MW' in VARIABLE.get("topologicalAddress"):
            # Récupération des l'adresse mémoire
            adresseSource = AdressNumber(VARIABLE.get("topologicalAddress"))

            # Récupération du type d'adresse mémoire
            TypeName = VARIABLE.get("typeName")

            # Recherche le types de données DDT dans l'arborescence
            childs = root.findall(".//DDTSource[@DDTName='" + TypeName + "']/structure/variables")


            folder = xml.Element("Folder")
            folder.set("name", VARIABLE.get("name"))
            RootXml.append(folder)

            # Generation de la variable en chaine
            ad = resolveDTT(root, VARIABLE.get("typeName"), "", VARIABLE.get("name"), adresseSource, "", None)

            CptVariable += 1

    OutputFile.close()

    tree = xml.ElementTree(RootXml)
    xml.indent(tree, ' ')
    with open("OutVijeo.xml", "wb") as files:
        tree.write(files, encoding='UTF-16', xml_declaration=True)

    print("")
    print("-------------------------------------------------------------------------------------------------")
    print("Variables trop longues")

    for Var in listName:
        print(Var + " => " + str(len(Var)))

    print("")
    print("___________________________________________________________________________________________________")
    print("|")
    print("|<> Conversion terminée :")
    print("|<> " + str(CptVariable) + " variables ont été analysées")
    print("|<> " + str(CptVariable2) + " variables ont été créés")
    print("|<!> " + str(len(listName)) + " variables n'ont pu être converties (Nom de variable > 32 caractères)")
    print("|__________________________________________________________________________________________________")

    os.system("pause")
