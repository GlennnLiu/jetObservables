import ROOT
import math, os, sys
import numpy as np
import fastjet
ROOT.PyConfig.IgnoreCommandLineOptions = True
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.tools import *

class nSubProd(Module):

    def __init__(self, selection='dijet', sysSource=[], leptonSF={}, year='2016', createTrees=False):
        self.writeHistFile=True
        self.createTrees=createTrees
        self.addSDJets=False
        self.addMoreSchemes=False
        self.leptonSFhelper = leptonSF
        print(self.leptonSFhelper)
        self.selection = selection
        self.year = year

        ### Kinematics Cuts AK8Jets ###
        self.minAK8JetPt = 170  ### this is the basic minimum, not the final
        self.maxJetAK8Eta = 2.4

        ### Cuts for selections
        self.minLeadAK8JetPtDijet = 450.
        self.minLeadAK8JetPtW = 200.
        self.minSDMassW = 60.   ### looser to pick low bins
        self.maxSDMassW = 120.  ### looser to pick higher bins
        self.minLeadAK8JetPtTop= 350.
        self.minSDMassTop = 140.
        self.METCutWtop = 40.

        ### Kinematics Cuts Jets ###
        self.minJetPt = 20
        self.maxJetEta = 2.4
        self.minBDisc = 0.7221  ### L: 0.0614, M: 0.3093, T: 07221

        ### Kinenatic Cuts Muons ###
        self.minMuonPt = 20.
        self.maxMuonEta = 2.4

        ### Kinenatic Cuts Electrons ###
        self.minElectronPt = 35.
        self.range1ElectronEta = [0,1.442]
        self.range2ElectronEta = [1.56,2.5]

        ### Defining nsubjetiness basis
        self.maxTau = 5
	self.nSub_labels = ["_tau_0p5_", "_tau_1_", "_tau_2_"]
        self.nSub0p5 = ROOT.NsubjettinessWrapper( 0.5, 0.8, 0, 0 ) #beta, cone size, measureDef 0=Normalize, axesDef 0=KT_axes
        self.nSub1 = ROOT.NsubjettinessWrapper( 1, 0.8, 0, 0 )
        self.nSub2 = ROOT.NsubjettinessWrapper( 2, 0.8, 0, 0 )
        self.nSub1_OP_kT = ROOT.NsubjettinessWrapper( 1, 0.8, 0, 6 ) ##### needed for genjet tau21 or tau32

        if self.addMoreSchemes:
            self.nSub0p5_WTA_kT = ROOT.NsubjettinessWrapper( 0.5, 0.8, 0, 3 ) #beta, cone size, measureDef 0=Normalize, axesDef 0=WTA_kT_axes
            self.nSub1_WTA_kT = ROOT.NsubjettinessWrapper( 1, 0.8, 0, 3 )
            self.nSub2_WTA_kT = ROOT.NsubjettinessWrapper( 2, 0.8, 0, 3 )

            self.nSub0p5_OP_kT = ROOT.NsubjettinessWrapper( 0.5, 0.8, 0, 6 ) #beta, cone size, measureDef 0=Normalize,axesDef 6=onepass_kT_axes
            self.nSub2_OP_kT = ROOT.NsubjettinessWrapper( 2, 0.8, 0, 6 )

        ### Softdrop quantities
        self.beta = 0.0
        self.zcut = 0.1
        self.R = 0.8
        self.sd = ROOT.SoftDropWrapper(self.beta, self.zcut, self.R, self.minAK8JetPt)

        print ("Load C++ Recluster worker module")
        ROOT.gSystem.Load("libPhysicsToolsNanoAODJMARTools.so")

        ### Helpers
	self.kinematic_labels = ["_pt", "_eta", "_phi", "_mass"]

        ### Uncerstinties
        self.sysSource = ['_nom'] + [ isys+i for i in [ 'Up', 'Down' ] for isys in sysSource if not isys.endswith('nom') ]
        ## JES from https://twiki.cern.ch/twiki/bin/view/CMS/JECUncertaintySources#Main_uncertainties_2016_80X
        self.JESLabels = [ "Total" ]
        #self.JESLabels = [ "AbsoluteStat", "AbsoluteScale", "AbsoluteMPFBias", "Fragmentation", "SinglePionECAL", "SinglePionHCAL", "FlavorQCD", "TimePtEta", "RelativeJEREC1", "RelativeJEREC2", "RelativeJERHF", "RelativePtBB", "RelativePtEC1", "RelativePtEC2", "RelativePtHF", "RelativeBal", "RelativeSample", "RelativeFSR", "RelativeStatFSR", "RelativeStatEC", "RelativeStatHF", "PileUpDataMC", "PileUpPtRef", "PileUpPtBB", "PileUpPtEC1", "PileUpPtEC2", "PileUpPtHF", "PileUpMuZero", "PileUpEnvelope", "SubTotalPileUp", "SubTotalRelative", "SubTotalPt", "SubTotalScale", "SubTotalAbsolute", "SubTotalMC", "Total", "TotalNoFlavor", "TotalNoTime", "TotalNoFlavorNoTime" ]

    #############################################################################
    def beginJob(self, histFile, histDirName):
        Module.beginJob(self, histFile, histDirName)

        tauBins = 100

        ### Booking histograms
        self.addObject( ROOT.TH1F('cutflow_reco',   ';cutflow_reco',   10, 0, 10) )
        self.addObject( ROOT.TH1F('cutflow_gen',   ';cutflow_gen',   10, 0, 10) )
        self.addObject( ROOT.TH1F('cutflowWeight_reco',   ';cutflowWeight_reco',   10, 0, 10) )
        self.addObject( ROOT.TH1F('cutflowWeight_gen',   ';cutflowWeight_gen',   10, 0, 10) )
        self.addObject( ROOT.TH1F('PUweight',   ';PUWeight',   20, 0, 2) )
        self.addObject( ROOT.TH1F('Lepweight',   ';LepWeight',   20, 0, 2) )
        #### general selection
        selList = (['_dijetSel' ] if self.selection.startswith('dijet') else [ '_WSel', '_topSel' ] )
        for isel in [ '_noSelnoWeight', '_noSel'] + selList:
            self.addObject( ROOT.TH1F('nPVs'+isel,   ';number of PVs',   100, 0, 100) )
            self.addObject( ROOT.TH1F('nleps'+isel,   ';number of leptons',   20, 0, 20) )
            self.addP4Hists( 'muons', isel )
            self.addP4Hists( 'eles', isel )
            self.addObject( ROOT.TH1F('nAK8jets'+isel,   ';number of AK8 jets',   20, 0, 20) )
            self.addP4Hists( 'AK8jets', isel )
            self.addObject( ROOT.TH1F('nAK4jets'+isel,   ';number of AK4 jets',   20, 0, 20) )
            self.addP4Hists( 'AK4jets', isel )
            self.addObject( ROOT.TH1F('METPt'+isel,   ';MET (GeV)',   200, 0, 2000) )
            self.addObject( ROOT.TH1F('HT'+isel,   ';HT (GeV)',   200, 0, 2000) )
            self.addObject( ROOT.TH1F('recoPtAsym'+isel,   '; pt Asymmetry', 100, 0, 1.) )
            self.addObject( ROOT.TH1F('recoDeltaPhi'+isel,   '; #Delta #Phi(j,j)', 100, 0, 5) )

            self.addObject( ROOT.TH1F('leadAK8JetMatched'+isel, ';AK8 reco jet SD mass matched'+isel+' [GeV]', 500, 0, 500) )

        for isel in [ '_noSel'] + selList:
            self.addObject( ROOT.TH1F('ngenleps'+isel,   ';number of gen leptons',   20, 0, 20) )
            self.addP4Hists( 'genmuons', isel )
            self.addP4Hists( 'geneles', isel )
            self.addObject( ROOT.TH1F('ngenAK8jets'+isel,   ';number of AK8 genjets',   20, 0, 20) )
            self.addP4Hists( 'AK8genjets', isel )
            self.addObject( ROOT.TH1F('ngenAK4jets'+isel,   ';number of AK4 genjets',   20, 0, 20) )
            self.addP4Hists( 'AK4genjets', isel )
            self.addObject( ROOT.TH1F('genMETPt'+isel,   ';gen MET (GeV)',   200, 0, 2000) )
            self.addObject( ROOT.TH1F('genHT'+isel,   ';genHT (GeV)',   200, 0, 2000) )
            self.addObject( ROOT.TH1F('genPtAsym'+isel,   '; pt Asymmetry', 100, 0, 1.) )
            self.addObject( ROOT.TH1F('genDeltaPhi'+isel,   '; #Delta #Phi(j,j)', 100, 0, 5) )

        for iSel in selList:
            self.addObject( ROOT.TH1F('cat'+iSel,   ';Number of True/Fake/Miss/others', 5, 0, 5) )

            nJet = [ 'Jet1', 'Jet2' ] if iSel.endswith('dijetSel') else [ 'Jet' ]

            for iJ in nJet:
                self.addP4Hists( 'reco'+iJ, iSel )
                self.addP4Hists( 'gen'+iJ, iSel )
                self.addObject( ROOT.TH1F('gen'+iJ+'Tau21'+iSel, ';AK8 gen jet #tau_{21}', tauBins, 0, 1) )
                self.addObject( ROOT.TH1F('gen'+iJ+'Tau32'+iSel, ';AK8 gen jet #tau_{32}', tauBins, 0, 1) )
                self.addObject( ROOT.TH1F('missgen'+iJ+'Pt'+iSel, ';AK8 missgen jet pt [GeV]', 500, 0, 5000) )
                self.addObject( ROOT.TH1F('missgen'+iJ+'Mass'+iSel, ';AK8 gen jet mass [GeV]', 500, 0, 500) )
                self.addObject( ROOT.TH1F('missgen'+iJ+'Eta'+iSel, ';AK8 missgen jet eta', 40, -5, 5) )
                self.addObject( ROOT.TH1F('missgen'+iJ+'Tau21'+iSel, ';AK8 missgen jet #tau_{21}', tauBins, 0, 1) )
                self.addObject( ROOT.TH1F('missgen'+iJ+'Tau32'+iSel, ';AK8 missgen jet #tau_{32}', tauBins, 0, 1) )
                if self.addSDJets:
                    self.addObject( ROOT.TH1F('genSD'+iJ+'Pt'+iSel, ';AK8 gen SD jet pt [GeV]', 500, 0, 5000) )
                    self.addObject( ROOT.TH1F('genSD'+iJ+'SDmass'+iSel, ';AK8 gen SD jet SD mass [GeV]', 500, 0, 500) )
                    self.addObject( ROOT.TH1F('genSD'+iJ+'Eta'+iSel, ';AK8 gen SD jet eta', tauBins, -5, 5) )
                    self.addObject( ROOT.TH1F('genSD'+iJ+'Tau21'+iSel, ';AK8 gen SD jet #tau_{21}', tauBins, 0, 1) )
                    self.addObject( ROOT.TH1F('genSD'+iJ+'Tau32'+iSel, ';AK8 gen SD jet #tau_{32}', tauBins, 0, 1) )

                for tauN in range(1, self.maxTau+1):
                    for x in self.nSub_labels:
                        if x.startswith(('1', '2')) and tauN>0:
                            maxValueTau=0.3
                            tauBins=300
                        else: maxValueTau=1
                        self.addObject( ROOT.TH1F('gen'+iJ+''+x+str(tauN)+iSel, ';AK8 genjet #tau', tauBins, 0, maxValueTau ) )
                        self.addObject( ROOT.TH1F('missgen'+iJ+''+x+str(tauN)+iSel, ';AK8 missgenjet #tau', tauBins, 0, maxValueTau ) )
                        if self.addMoreSchemes:
                            self.addObject( ROOT.TH1F('gen'+iJ+''+x+str(tauN)+'_WTA_kT'+iSel, ';AK8 genjet #tau', tauBins, 0, maxValueTau ) )
                            self.addObject( ROOT.TH1F('gen'+iJ+''+x+str(tauN)+'_OP_kT'+iSel, ';AK8 genjet #tau', tauBins, 0, maxValueTau ) )
                            self.addObject( ROOT.TH1F('missgen'+iJ+''+x+str(tauN)+'_WTA_kT'+iSel, ';AK8 missgenjet #tau', tauBins, 0, maxValueTau ) )
                            self.addObject( ROOT.TH1F('missgen'+iJ+''+x+str(tauN)+'_OP_kT'+iSel, ';AK8 missgenjet #tau', tauBins, 0, maxValueTau ) )
                        if self.addSDJets:
                            self.addObject( ROOT.TH1F('genSD'+iJ+''+x+str(tauN)+iSel, ';AK8 genjet #tau', tauBins, 0, maxValueTau ) )
                            if self.addMoreSchemes:
                                self.addObject( ROOT.TH1F('genSD'+iJ+''+x+str(tauN)+'_WTA_kT'+iSel, ';AK8 genjet #tau', tauBins, 0, maxValueTau ) )
                                self.addObject( ROOT.TH1F('genSD'+iJ+''+x+str(tauN)+'_OP_kT'+iSel, ';AK8 genjet #tau', tauBins, 0, maxValueTau ) )

                for sysUnc in self.sysSource:
                    self.addObject( ROOT.TH1F('reco'+iJ+'Pt'+sysUnc+iSel, ';AK8 reco jet pt [GeV]', 500, 0, 5000) )
                    self.addObject( ROOT.TH1F('reco'+iJ+'SDmass'+sysUnc+iSel, ';AK8 reco jet SD mass [GeV]', 500, 0, 500) )
                    self.addObject( ROOT.TH1F('reco'+iJ+'Eta'+sysUnc+iSel, ';AK8 reco jet eta', 40, -5, 5) )
                    self.addObject( ROOT.TH1F('fakereco'+iJ+'Pt'+sysUnc+iSel, ';AK8 fakereco jet pt [GeV]', 500, 0, 5000) )
                    self.addObject( ROOT.TH1F('fakereco'+iJ+'SDmass'+sysUnc+iSel, ';AK8 fakereco jet SD mass [GeV]', 500, 0, 500) )
                    self.addObject( ROOT.TH1F('fakereco'+iJ+'Eta'+sysUnc+iSel, ';AK8 fakereco jet eta', 40, -5, 5) )
                    self.addObject( ROOT.TH1F('reco'+iJ+'Tau21'+sysUnc+iSel, ';AK8 reco jet #tau_{21}', tauBins, 0, 1) )
                    self.addObject( ROOT.TH1F('fakereco'+iJ+'Tau21'+sysUnc+iSel, ';AK8 fakereco jet #tau_{21}', tauBins, 0, 1) )
                    self.addObject( ROOT.TH2F('resp'+iJ+'Tau21'+sysUnc+iSel, ';AK8 gen jet #tau_{21};AK8 reco jet #tau_{21}', tauBins, 0, 1, tauBins, 0, 1) )
                    self.addObject( ROOT.TH1F('reco'+iJ+'Tau32'+sysUnc+iSel, ';AK8 reco jet #tau_{32}', tauBins, 0, 1) )
                    self.addObject( ROOT.TH1F('fakereco'+iJ+'Tau32'+sysUnc+iSel, ';AK8 fakereco jet #tau_{32}', tauBins, 0, 1) )
                    self.addObject( ROOT.TH2F('resp'+iJ+'Tau32'+sysUnc+iSel, ';AK8 gen jet #tau_{32};AK8 reco jet #tau_{32}', tauBins, 0, 1, tauBins, 0, 1) )
                    if sysUnc.endswith('nom'):
                        self.addObject( ROOT.TH1F('resol'+iJ+'Pt'+iSel, ';AK8 reco/gen jet pt', 100, 0, 2) )
                        self.addObject( ROOT.TH1F('resol'+iJ+'SDmass'+iSel, ';AK8 reco/gen jet SD mass', 100, 0, 2) )
                        self.addObject( ROOT.TH1F('resol'+iJ+'Tau21'+iSel, ';AK8 reco/gen jet #tau_{21}', 100, 0, 2) )
                        self.addObject( ROOT.TH1F('resol'+iJ+'Tau32'+iSel, ';AK8 reco/gen jet #tau_{32}', 100, 0, 2) )

                    if self.addSDJets:
                        self.addObject( ROOT.TH1F('recoSD'+iJ+'Pt'+sysUnc+iSel, ';AK8 reco SD jet pt [GeV]', 500, 0, 5000) )
                        self.addObject( ROOT.TH1F('recoSD'+iJ+'SDmass'+sysUnc+iSel, ';AK8 reco SD jet SD mass [GeV]', 500, 0, 500) )
                        self.addObject( ROOT.TH1F('recoSD'+iJ+'Eta'+sysUnc+iSel, ';AK8 reco SD jet eta', tauBins, -5, 5) )
                        self.addObject( ROOT.TH1F('recoSD'+iJ+'Tau21'+sysUnc+iSel, ';AK8 reco SD jet #tau_{21}', tauBins, 0, 1) )
                        self.addObject( ROOT.TH2F('respSD'+iJ+'Tau21'+sysUnc+iSel, ';AK8 gen jet #tau_{21};AK8 reco SD jet #tau_{21}', tauBins, 0, 1, tauBins, 0, 1) )
                        self.addObject( ROOT.TH1F('recoSD'+iJ+'Tau32'+sysUnc+iSel, ';AK8 reco SD jet #tau_{32}', tauBins, 0, 1) )
                        self.addObject( ROOT.TH2F('respSD'+iJ+'Tau32'+sysUnc+iSel, ';AK8 gen jet #tau_{32};AK8 reco SD jet #tau_{32}', tauBins, 0, 1, tauBins, 0, 1) )

                    for tauN in range(1, self.maxTau+1):
                        for x in self.nSub_labels:
                            if x.startswith(('1', '2')) and tauN>0:
                                maxValueTau=0.3
                                tauBins=300
                            else: maxValueTau=1
                            self.addObject( ROOT.TH1F('reco'+iJ+x+str(tauN)+sysUnc+iSel, ';AK8 jet #tau', tauBins, 0, maxValueTau ) )
                            self.addObject( ROOT.TH1F('fakereco'+iJ+x+str(tauN)+sysUnc+iSel, ';AK8 jet #tau', tauBins, 0, maxValueTau ) )
                            self.addObject( ROOT.TH2F('resp'+iJ+x+str(tauN)+sysUnc+iSel, ';AK8 gen jet #tau_{'+str(tauN)+'};AK8 reco jet #tau_{'+str(tauN)+'}', tauBins, 0, maxValueTau, tauBins, 0, maxValueTau) )
                            if sysUnc.endswith('nom'): self.addObject( ROOT.TH1F('resol'+iJ+x+str(tauN)+iSel, ';AK8 reco/gen jet #tau_{'+str(tauN)+'}', 100, 0, 2) )

                            if self.addMoreSchemes:
                                self.addObject( ROOT.TH1F('reco'+iJ+x+str(tauN)+'_WTA_kT'+sysUnc+iSel, ';AK8 jet #tau', tauBins, 0, maxValueTau ) )
                                self.addObject( ROOT.TH1F('fakereco'+iJ+x+str(tauN)+'_WTA_kT'+sysUnc+iSel, ';AK8 jet #tau', tauBins, 0, maxValueTau ) )
                                self.addObject( ROOT.TH2F('resp'+iJ+x+str(tauN)+'_WTA_kT'+sysUnc+iSel, ';AK8 gen jet #tau_{'+str(tauN)+'};AK8 reco jet #tau_{'+str(tauN)+'}', tauBins, 0, maxValueTau, tauBins, 0, maxValueTau) )

                                self.addObject( ROOT.TH1F('reco'+iJ+x+str(tauN)+'_OP_kT'+sysUnc+iSel, ';AK8 jet #tau', tauBins, 0, maxValueTau ) )
                                self.addObject( ROOT.TH1F('fakereco'+iJ+x+str(tauN)+'_OP_kT'+sysUnc+iSel, ';AK8 jet #tau', tauBins, 0, maxValueTau ) )
                                self.addObject( ROOT.TH2F('resp'+iJ+x+str(tauN)+'_OP_kT'+sysUnc+iSel, ';AK8 gen jet #tau_{'+str(tauN)+'};AK8 reco jet #tau_{'+str(tauN)+'}', tauBins, 0, maxValueTau, tauBins, 0, maxValueTau) )

                            if self.addSDJets:
                                self.addObject( ROOT.TH1F('recoSD'+iJ+x+str(tauN)+sysUnc+iSel, ';AK8 jet #tau', tauBins, 0, maxValueTau ) )
                                self.addObject( ROOT.TH2F('respSD'+iJ+x+str(tauN)+sysUnc+iSel, ';AK8 gen jet #tau_{'+str(tauN)+'};AK8 reco SD jet #tau_{'+str(tauN)+'}', tauBins, 0, maxValueTau, tauBins, 0, maxValueTau) )

                                if self.addMoreSchemes:
                                    self.addObject( ROOT.TH1F('recoSD'+iJ+x+str(tauN)+'_WTA_kT'+sysUnc+iSel, ';AK8 jet #tau', tauBins, 0, maxValueTau ) )
                                    self.addObject( ROOT.TH2F('respSD'+iJ+x+str(tauN)+'_WTA_kT'+sysUnc+iSel, ';AK8 gen jet #tau_{'+str(tauN)+'};AK8 reco SD jet #tau_{'+str(tauN)+'}', tauBins, 0, maxValueTau, tauBins, 0, maxValueTau) )

                                    self.addObject( ROOT.TH1F('recoSD'+iJ+x+str(tauN)+'_OP_kT'+sysUnc+iSel, ';AK8 jet #tau', tauBins, 0, maxValueTau ) )
                                    self.addObject( ROOT.TH2F('respSD'+iJ+x+str(tauN)+'_OP_kT'+sysUnc+iSel, ';AK8 gen jet #tau_{'+str(tauN)+'};AK8 reco SD jet #tau_{'+str(tauN)+'}', tauBins, 0, maxValueTau, tauBins, 0, maxValueTau) )

    #############################################################################
    def addP4Hists(self, s, t ):
        self.addObject( ROOT.TH1F(s+'_pt'+t,  s+';p_{T} (GeV)',   200, 0, 2000) )
        self.addObject( ROOT.TH1F(s+'_eta'+t, s+';#eta', 100, -4.0, 4.0 ) )
        self.addObject( ROOT.TH1F(s+'_phi'+t, s+';#phi', 100, -3.14259, 3.14159) )
        self.addObject( ROOT.TH1F(s+'_mass'+t,s+';mass (GeV)', 100, 0, 1000) )


    #############################################################################
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):

        if self.createTrees:
            self.out = wrappedOutputTree
            self.out.branch('leptonWeight',  "F")
            for ijet in ["0"]: #,1] :
                for x in self.kinematic_labels:
                    self.out.branch("goodrecojet" + ijet + "%s"%x,  "F")
                    if not x.startswith(('_eta', '_phi')):
                        for u in [ 'Up', 'Down' ]:
                            self.out.branch("goodrecojet" + ijet + "%s"%x+'_jer'+u,  "F")
                            for jes in self.JESLabels:
                                self.out.branch("goodrecojet" + ijet + "%s"%x+'_jesUnc'+jes+u,  "F")

                self.out.branch("goodrecojet" + ijet + '_Sel',  "I")
                self.out.branch("ngoodrecojet" + ijet,  "I")  ### dummy for nanoAOD Tools
                self.out.branch("goodrecojet" + ijet + '_pt_raw',  "F")
                self.out.branch("goodrecojet" + ijet + '_mass_raw',  "F")
                self.out.branch("goodrecojet" + ijet + '_corr_JEC',  "F")
                self.out.branch("goodrecojet" + ijet + '_corr_JER',  "F")
                self.out.branch("goodrecojet" + ijet + '_corr_JMS',  "F")
                self.out.branch("goodrecojet" + ijet + '_corr_JMR',  "F")
                self.out.branch("goodrecojet" + ijet + '_mass_jmrUp',  "F")
                self.out.branch("goodrecojet" + ijet + '_mass_jmsUp',  "F")
                self.out.branch("goodrecojet" + ijet + '_mass_jmrDown',  "F")
                self.out.branch("goodrecojet" + ijet + '_mass_jmsDown',  "F")
                self.out.branch("goodrecojet" + ijet + "_softdrop_mass",  "F")
                self.out.branch("goodrecojet" + ijet + "_tau21",  "F")
                self.out.branch("goodrecojet" + ijet + "_N21",  "F")

                self.out.branch("goodgenjet" + ijet + '_Sel',  "I")
                self.out.branch("ngoodgenjet" + ijet,  "I")  ### dummy for nanoAOD Tools
                self.out.branch("nsd_goodgenjet" + ijet,  "I")
                for x in self.kinematic_labels:
                    self.out.branch("goodgenjet" + ijet + "%s"%x,  "F")
                    self.out.branch("sd_goodgenjet" + ijet + "%s"%x,  "F")
                self.out.branch("goodgenjet" + ijet + "_tau21", "F")
                self.out.branch("sd_goodgenjet" + ijet + "_tau21", "F")

                self.out.branch("dR_gen_reco_AK8", "F")
                self.out.branch("dR_genW_genAK8", "F")
                self.out.branch("genEventNo_taus_are_0",  "I")

                for x in self.kinematic_labels:
                    self.out.branch("sd_goodrecojet" + ijet + "%s"%x,  "F")
                self.out.branch("nsd_goodrecojet" + ijet,  "I")  ### dummy for nanoAOD Tools
                self.out.branch("sd_goodrecojet" + ijet + "_tau21",  "F")

                for tauN in range(1, self.maxTau+1):
                    for x in self.nSub_labels:

                        self.out.branch("goodrecojet" + ijet + "%s"%x +str(tauN),  "F")
                        self.out.branch("goodgenjet" + ijet + "%s"%x +str(tauN),  "F")

                        self.out.branch("goodrecojet" + ijet + "%s"%x +str(tauN) + "_WTA_kT",  "F")
                        self.out.branch("goodgenjet" + ijet + "%s"%x +str(tauN) + "_WTA_kT",  "F")

                        self.out.branch("goodrecojet" + ijet + "%s"%x +str(tauN) + "_OP_kT",  "F")
                        self.out.branch("goodgenjet" + ijet + "%s"%x +str(tauN) + "_OP_kT",  "F")

                        self.out.branch("sd_goodrecojet" + ijet + "%s"%x +str(tauN),  "F")
                        self.out.branch("sd_goodgenjet" + ijet + "%s"%x +str(tauN),  "F")

                        self.out.branch("sd_goodrecojet" + ijet + "%s"%x +str(tauN) + "_WTA_kT",  "F")
                        self.out.branch("sd_goodgenjet" + ijet + "%s"%x +str(tauN) + "_WTA_kT",  "F")

                        self.out.branch("sd_goodrecojet" + ijet + "%s"%x +str(tauN) + "_OP_kT",  "F")
                        self.out.branch("sd_goodgenjet" + ijet + "%s"%x +str(tauN) + "_OP_kT",  "F")
        pass


    #############################################################################
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    #############################################################################
    def leptonSF(self, lepton, leptonP4 ):

        if lepton.startswith("muon"): leptonP4eta = abs(leptonP4.eta)
        else: leptonP4eta = leptonP4.eta

        SFFileTrigger = ROOT.TFile( os.environ['CMSSW_BASE']+"/src/jetObservables/Skimmer/data/"+self.leptonSFhelper[lepton]['Trigger'][0] )
        histoSFTrigger = SFFileTrigger.Get( self.leptonSFhelper[lepton]['Trigger'][1] )
        SFTrigger = histoSFTrigger.GetBinContent( histoSFTrigger.GetXaxis().FindBin( leptonP4.pt ), histoSFTrigger.GetYaxis().FindBin( leptonP4eta ) )

        SFFileID = ROOT.TFile( os.environ['CMSSW_BASE']+"/src/jetObservables/Skimmer/data/"+self.leptonSFhelper[lepton]['ID'][0] )
        histoSFID = SFFileID.Get( self.leptonSFhelper[lepton]['ID'][1] )
        histoSFID_X = histoSFID.GetXaxis().FindBin( leptonP4.pt if self.leptonSFhelper[lepton]['ID'][2] else leptonP4eta )
        histoSFID_Y = histoSFID.GetYaxis().FindBin( leptonP4eta if self.leptonSFhelper[lepton]['ID'][2] else leptonP4.pt )
        SFID = histoSFID.GetBinContent( histoSFID_X, histoSFID_Y )
        SFID = SFID if SFID>0 else 1

        if self.year.startswith('2016') and lepton.startswith("muon"): leptonP4eta = leptonP4.eta    #### stupid fix for the stupid SF file
        SFFileISO = ROOT.TFile( os.environ['CMSSW_BASE']+"/src/jetObservables/Skimmer/data/"+self.leptonSFhelper[lepton]['ISO'][0] )
        histoSFISO = SFFileISO.Get( self.leptonSFhelper[lepton]['ISO'][1] )
        histoSFISO_X = histoSFISO.GetXaxis().FindBin( leptonP4.pt if self.leptonSFhelper[lepton]['ISO'][2] else leptonP4eta )
        histoSFISO_Y = histoSFISO.GetYaxis().FindBin( leptonP4eta if self.leptonSFhelper[lepton]['ISO'][2] else leptonP4.pt )
        SFISO = histoSFISO.GetBinContent( histoSFISO_X, histoSFISO_Y )
        SFISO = SFISO if SFISO>0 else 1

        #print (SFTrigger * SFID * SFISO), SFTrigger , SFID , SFISO, leptonP4.pt, leptonP4.eta
        return [SFTrigger , SFID , SFISO]


    #############################################################################
    def analyze(self, event):
        '''process event, return True (go to next module) or False (fail, go to next event)'''

        self.isMC = event.run == 1

        ##### Reco analysis selection
        genJet = self.genSelection(event) if self.isMC else {}
        recoJet = self.recoSelection( event, genJet )
        if self.createTrees: self.fillBranches( recoJet, genJet )       ### comment it to reduce RAM

        return True


    #############################################################################
    def recoSelection( self, event, genAK8jet ):
        '''Analyzing reco information'''

        AK8jets = list(Collection(event, 'FatJet' ))
        electrons = list(Collection(event, 'Electron'))
        muons = list(Collection(event, 'Muon'))
        jets = list(Collection(event, 'Jet'))
        met = Object(event, 'MET')

        #### Lepton selection
        recoElectrons  = [x for x in electrons if x.pt>self.minElectronPt and x.cutBased_HEEP and ((self.range1ElectronEta[0]<abs(x.eta)<self.range1ElectronEta[1]) or (self.range2ElectronEta[0]<abs(x.eta)<self.range2ElectronEta[1]))]
        recoElectrons.sort(key=lambda x:x.pt, reverse=True)

        recoMuons = [ x for x in muons if x.pt > self.minMuonPt and x.highPtId > 1 and abs(x.p4().Eta()) < self.maxMuonEta and x.pfRelIso03_all < 0.1]
        recoMuons.sort(key=lambda x:x.pt, reverse=True)
        nleptons = len(recoMuons)+len(recoElectrons)
        ##################################################

        #### MET (not sure if needed)
        MET = ROOT.TLorentzVector()
        MET.SetPtEtaPhiE(met.pt, 0., met.phi, met.sumEt)
        ##################################################

        #### Basic AK8 jet selection
        recoAK8jets = [ x for x in AK8jets if x.pt_nom > self.minAK8JetPt and abs(x.eta) < self.maxJetAK8Eta ] # and x.jetId>4]
        AK8HT = sum( [ x.pt for x in recoAK8jets ] )
        recoAK8jets.sort(key=lambda x:x.pt_nom,reverse=True)
        ##################################################

        #### Basic AK4 bjet selection
        recoAK4bjets = [ x for x in jets if x.pt > self.minJetPt and abs(x.eta) < self.maxJetEta and x.btagDeepB > self.minBDisc ] # and x.jetId>4 ]
        recoAK4bjets.sort(key=lambda x:x.pt,reverse=True)
        ##################################################

        #### Weight
        if self.isMC and self.selection.startswith('Wtop'):
            if len(recoMuons)>0: leptonWeights= self.leptonSF( "muon", recoMuons[0] )
            else: leptonWeights = [0, 0, 0]
        else: leptonWeights = [1, 1, 1]

        if self.isMC:
            weight = event.puWeight * event.genWeight * np.prod(leptonWeights)
            getattr( self, 'PUweight' ).Fill( event.puWeight )
            getattr( self, 'Lepweight' ).Fill( np.prod(leptonWeights) )
            self.leptonWeight = np.prod(leptonWeights)
            if self.createTrees: self.out.fillBranch("leptonWeight", np.prod(leptonWeights) )  ### dummy for nanoAOD Tools
        else:
            weight = 1
            self.leptonWeight = 1
        ##################################################

        #### Checking no selection without weights
        getattr( self, 'nPVs_noSelnoWeight' ).Fill( getattr( event, 'PV_npvsGood') )
        getattr( self, 'nleps_noSelnoWeight' ).Fill( nleptons )
        for imuon in recoMuons:
            getattr( self, 'muons_pt_noSelnoWeight' ).Fill( imuon.pt )
            getattr( self, 'muons_eta_noSelnoWeight' ).Fill( imuon.eta )
            getattr( self, 'muons_phi_noSelnoWeight' ).Fill( imuon.phi )
        for iele in recoElectrons:
            getattr( self, 'eles_pt_noSelnoWeight' ).Fill( iele.pt )
            getattr( self, 'eles_eta_noSelnoWeight' ).Fill( iele.eta )
            getattr( self, 'eles_phi_noSelnoWeight' ).Fill( iele.phi )
        getattr( self, 'nAK8jets_noSelnoWeight' ).Fill( len(recoAK8jets) )
        getattr( self, 'HT_noSelnoWeight' ).Fill( AK8HT )
        for ijet in recoAK8jets:
            getattr( self, 'AK8jets_pt_noSelnoWeight' ).Fill( ijet.pt )
            getattr( self, 'AK8jets_eta_noSelnoWeight' ).Fill( ijet.eta )
            getattr( self, 'AK8jets_phi_noSelnoWeight' ).Fill( ijet.phi )
            getattr( self, 'AK8jets_mass_noSelnoWeight' ).Fill( ijet.msoftdrop )
        getattr( self, 'nAK4jets_noSelnoWeight' ).Fill( len(recoAK4bjets) )
        for ijet in recoAK4bjets:
            getattr( self, 'AK4jets_pt_noSelnoWeight' ).Fill( ijet.pt )
            getattr( self, 'AK4jets_eta_noSelnoWeight' ).Fill( ijet.eta )
            getattr( self, 'AK4jets_phi_noSelnoWeight' ).Fill( ijet.phi )
        getattr( self, 'METPt_noSelnoWeight' ).Fill( MET.Pt() )

        #### Checking no selection with weights
        getattr( self, 'nPVs_noSel' ).Fill( getattr( event, 'PV_npvsGood'), weight )
        getattr( self, 'nleps_noSel' ).Fill( nleptons, weight )
        for imuon in recoMuons:
            getattr( self, 'muons_pt_noSel' ).Fill( imuon.pt, weight )
            getattr( self, 'muons_eta_noSel' ).Fill( imuon.eta, weight )
            getattr( self, 'muons_phi_noSel' ).Fill( imuon.phi, weight )
        for iele in recoElectrons:
            getattr( self, 'eles_pt_noSel' ).Fill( iele.pt, weight )
            getattr( self, 'eles_eta_noSel' ).Fill( iele.eta, weight )
            getattr( self, 'eles_phi_noSel' ).Fill( iele.phi, weight )
        getattr( self, 'nAK8jets_noSel' ).Fill( len(recoAK8jets), weight )
        getattr( self, 'HT_noSel' ).Fill( AK8HT, weight )
        for ijet in recoAK8jets:
            getattr( self, 'AK8jets_pt_noSel' ).Fill( ijet.pt, weight )
            getattr( self, 'AK8jets_eta_noSel' ).Fill( ijet.eta, weight )
            getattr( self, 'AK8jets_phi_noSel' ).Fill( ijet.phi, weight )
            getattr( self, 'AK8jets_mass_noSel' ).Fill( ijet.msoftdrop, weight )
        getattr( self, 'nAK4jets_noSel' ).Fill( len(recoAK4bjets), weight )
        for ijet in recoAK4bjets:
            getattr( self, 'AK4jets_pt_noSel' ).Fill( ijet.pt, weight )
            getattr( self, 'AK4jets_eta_noSel' ).Fill( ijet.eta, weight )
            getattr( self, 'AK4jets_phi_noSel' ).Fill( ijet.phi, weight )
        getattr( self, 'METPt_noSel' ).Fill( MET.Pt(), weight )
        ptAsym = ( recoAK8jets[0].pt - recoAK8jets[1].pt ) / (recoAK8jets[0].pt + recoAK8jets[1].pt) if len(recoAK8jets)>1 else 0
        deltaPhi = recoAK8jets[0].p4().DeltaPhi( recoAK8jets[1].p4() ) if len(recoAK8jets)>1 else 0
        getattr( self, 'recoPtAsym_noSel' ).Fill( ptAsym, weight )
        getattr( self, 'recoDeltaPhi_noSel' ).Fill( deltaPhi, weight )

        ##### Applying selection
        iSel = None
        recoAK8jetInfo = {}
        getattr( self, 'cutflow_reco' ).Fill( 0 )
        getattr( self, 'cutflowWeight_reco' ).Fill( 0, weight )

        if self.selection.startswith('dijet'):

            if (len(recoMuons)+len(recoElectrons)==0) and (len(recoAK8jets)>1) and (ptAsym<0.3) and (deltaPhi>2) and ( recoAK8jets[1].pt>self.minLeadAK8JetPtDijet):          ### PT REQUIREMENT NEEDS TO BE REVISIT
                iSel = '_dijetSel'
                minLeadAK8JetPt = self.minLeadAK8JetPtDijet
                if self.createTrees: self.out.fillBranch( 'goodrecojet0_Sel', 2 )
                getattr( self, 'cutflow_reco' ).Fill( 2 )
                getattr( self, 'cutflowWeight_reco' ).Fill( 2, weight )
                tmpJet1 = recoAK8jets[0] if abs(recoAK8jets[0].eta) > abs(recoAK8jets[1].eta) else recoAK8jets[1]
                tmpJet2 = recoAK8jets[1] if abs(recoAK8jets[0].eta) > abs(recoAK8jets[1].eta) else recoAK8jets[0]
                recoAK8jetInfo['Jet1'] = self.createNsubBasis( iSel, tmpJet1, self.minLeadAK8JetPtDijet, event, 'PFCandsAK8' )
                recoAK8jetInfo['Jet2'] = self.createNsubBasis( iSel, tmpJet2, self.minLeadAK8JetPtDijet, event, 'PFCandsAK8' )
            else:
                if self.createTrees: self.out.fillBranch( 'goodrecojet0_Sel', 0 )

        elif self.selection.startswith('Wtop'):

            if (len(recoMuons)==1) and (len(recoAK8jets)>0) and (len(recoAK4bjets)>1) and (met.pt>self.METCutWtop):

                ### removing ak4 jets inside leadAK8 jet
                for bjet in recoAK4bjets:
                    if recoAK8jets[0].p4().DeltaR( bjet.p4() )<0.8 : recoAK4bjets.remove(bjet)

                ### defining muon isolation and leptonic top
                muonIso = []
                leptonicTop = []
                for bjet in recoAK4bjets:
                    if bjet.p4().DeltaR( recoMuons[0].p4() )<0.4: muonIso.append( False )
                    if (recoMuons[0].p4().DeltaR( bjet.p4() )>0.4) and (recoMuons[0].p4().DeltaR( bjet.p4() )<1.5): leptonicTop.append( True )

                if all(muonIso) and ((MET+recoMuons[0].p4()).Pt()>200) and any(leptonicTop) and (recoAK8jets[0].p4().DeltaR(recoMuons[0].p4())>0.8) and (len(recoAK4bjets)>1):

                    if (recoAK8jets[0].msoftdrop<self.maxSDMassW) and (recoAK8jets[0].msoftdrop>self.minSDMassW):
                        iSel = '_WSel'
                        minLeadAK8JetPt = self.minLeadAK8JetPtW
                        if self.createTrees: self.out.fillBranch( 'goodrecojet0_Sel', 4 )
                        getattr( self, 'cutflow_reco' ).Fill( 4 )
                        getattr( self, 'cutflowWeight_reco' ).Fill( 4, weight )
                        recoAK8jetInfo['Jet'] = self.createNsubBasis( iSel, recoAK8jets[0], self.minLeadAK8JetPtW, event, 'PFCandsAK8' )

                    elif (recoAK8jets[0].msoftdrop>self.minSDMassTop):
                        iSel = '_topSel'
                        minLeadAK8JetPt = self.minLeadAK8JetPtTop
                        if self.createTrees: self.out.fillBranch( 'goodrecojet0_Sel', 6 )
                        getattr( self, 'cutflow_reco' ).Fill( 6 )
                        getattr( self, 'cutflowWeight_reco' ).Fill( 6, weight )
                        recoAK8jetInfo['Jet'] = self.createNsubBasis( iSel, recoAK8jets[0], self.minLeadAK8JetPtTop, event, 'PFCandsAK8' )

                    else:
                        if self.createTrees: self.out.fillBranch( 'goodrecojet0_Sel', 8 )
                        getattr( self, 'cutflow_reco' ).Fill( 8 )
                        getattr( self, 'cutflowWeight_reco' ).Fill( 8, weight )

            else:
                if self.createTrees: self.out.fillBranch( 'goodrecojet0_Sel', 0 )


        #### Creating Nsub basis, filling histos and creating branches IF iSel
        if (len(recoAK8jetInfo)>0) and ('jet' in recoAK8jetInfo[next(iter(recoAK8jetInfo))]):     ### similar as if iSel

            #### Basic reco histos
            getattr( self, 'nPVs'+iSel ).Fill( getattr( event, 'PV_npvsGood'), weight )
            getattr( self, 'nleps'+iSel ).Fill( len(recoMuons)+len(recoElectrons), weight )
            for imuon in recoMuons:
                getattr( self, 'muons_pt'+iSel ).Fill( imuon.pt, weight )
                getattr( self, 'muons_eta'+iSel ).Fill( imuon.eta, weight )
                getattr( self, 'muons_phi'+iSel ).Fill( imuon.phi, weight )
            for iele in recoElectrons:
                getattr( self, 'eles_pt'+iSel ).Fill( iele.pt, weight )
                getattr( self, 'eles_eta'+iSel ).Fill( iele.eta, weight )
                getattr( self, 'eles_phi'+iSel ).Fill( iele.phi, weight )
            getattr( self, 'nAK8jets'+iSel ).Fill( len(recoAK8jets), weight )
            getattr( self, 'HT'+iSel ).Fill( AK8HT, weight )
            for ijet in recoAK8jets:
                getattr( self, 'AK8jets_pt'+iSel ).Fill( ijet.pt, weight )
                getattr( self, 'AK8jets_eta'+iSel ).Fill( ijet.eta, weight )
                getattr( self, 'AK8jets_phi'+iSel ).Fill( ijet.phi, weight )
                getattr( self, 'AK8jets_mass'+iSel ).Fill( ijet.msoftdrop, weight )
            getattr( self, 'nAK4jets'+iSel ).Fill( len(recoAK4bjets), weight )
            for ijet in recoAK4bjets:
                getattr( self, 'AK4jets_pt'+iSel ).Fill( ijet.pt, weight )
                getattr( self, 'AK4jets_eta'+iSel ).Fill( ijet.eta, weight )
                getattr( self, 'AK4jets_phi'+iSel ).Fill( ijet.phi, weight )
            getattr( self, 'METPt'+iSel ).Fill( getattr(event,'MET_pt'), weight )
            getattr( self, 'recoPtAsym'+iSel ).Fill( ptAsym, weight )
            getattr( self, 'recoDeltaPhi'+iSel ).Fill( deltaPhi, weight )

            if len(genAK8jet)==len(recoAK8jetInfo):
                isfakeJet = False
                getattr( self, 'cat'+iSel ).Fill( 1 )
            else:
                isfakeJet = True
                getattr( self, 'cat'+iSel ).Fill( 3 )

            ##### Filling histograms
            for iJ, ireco in recoAK8jetInfo.iteritems():
                for sysUnc in self.sysSource:
                    if ( getattr(ireco['jet'], 'pt'+(sysUnc if not sysUnc.startswith('_pu') else '_nom')) > minLeadAK8JetPt ):

                        if sysUnc.endswith('nom'):
                            getattr( self, 'reco'+iJ+'_pt'+iSel ).Fill( getattr(ireco['jet'], 'pt'), weight )
                            getattr( self, 'reco'+iJ+'_eta'+iSel ).Fill( getattr(ireco['jet'], 'eta'), weight )
                            getattr( self, 'reco'+iJ+'_phi'+iSel ).Fill( getattr(ireco['jet'], 'phi'), weight )
                            getattr( self, 'reco'+iJ+'_mass'+iSel ).Fill( getattr(ireco['jet'], 'msoftdrop'), weight )

                        if sysUnc.startswith('_pu'):
                            WEIGHT = event.genWeight * self.leptonWeight * getattr( event, 'puWeight'+sysUnc.split('pu')[1] )
                            getattr( self, ('fakereco' if isfakeJet else 'reco')+iJ+'Pt'+sysUnc+iSel ).Fill( getattr(ireco['jet'], 'pt_nom' ), WEIGHT )
                            getattr( self, ('fakereco' if isfakeJet else 'reco')+iJ+'SDmass'+sysUnc+iSel ).Fill( getattr(ireco['jet'], 'msoftdrop_nom' ), WEIGHT )
                        else:
                            WEIGHT =  weight
                            getattr( self, ('fakereco' if isfakeJet else 'reco')+iJ+'Pt'+sysUnc+iSel ).Fill( getattr(ireco['jet'], 'pt'+sysUnc ), WEIGHT )
                            getattr( self, ('fakereco' if isfakeJet else 'reco')+iJ+'SDmass'+sysUnc+iSel ).Fill( getattr(ireco['jet'], 'msoftdrop'+sysUnc ), WEIGHT )
                        getattr( self, ('fakereco' if isfakeJet else 'reco')+iJ+'Eta'+sysUnc+iSel ).Fill( getattr(ireco['jet'], 'eta'), WEIGHT )
                        getattr( self, ('fakereco' if isfakeJet else 'reco')+iJ+'Tau21'+sysUnc+iSel ).Fill( ireco['tau21'], WEIGHT )
                        getattr( self, ('fakereco' if isfakeJet else 'reco')+iJ+'Tau32'+sysUnc+iSel ).Fill( ireco['tau32'], WEIGHT )
                        for tauN in range(1, self.maxTau+1):
                            getattr( self, ('fakereco' if isfakeJet else 'reco')+iJ+'_tau_0p5_'+str(tauN)+sysUnc+iSel ).Fill( ireco['0p5'+str(tauN)], WEIGHT )
                            getattr( self, ('fakereco' if isfakeJet else 'reco')+iJ+'_tau_1_'+str(tauN)+sysUnc+iSel ).Fill( ireco['1'+str(tauN)], WEIGHT )
                            getattr( self, ('fakereco' if isfakeJet else 'reco')+iJ+'_tau_2_'+str(tauN)+sysUnc+iSel ).Fill( ireco['2'+str(tauN)], WEIGHT )
                            if self.addMoreSchemes:
                                getattr( self, ('fakereco' if isfakeJet else 'reco')+iJ+'_tau_0p5_'+str(tauN)+'_WTA_kT'+sysUnc+iSel ).Fill( ireco['0p5WTAkT'+str(tauN)], WEIGHT )
                                getattr( self, ('fakereco' if isfakeJet else 'reco')+iJ+'_tau_1_'+str(tauN)+'_WTA_kT'+sysUnc+iSel ).Fill( ireco['1WTAkT'+str(tauN)], WEIGHT )
                                getattr( self, ('fakereco' if isfakeJet else 'reco')+iJ+'_tau_2_'+str(tauN)+'_WTA_kT'+sysUnc+iSel ).Fill( ireco['2WTAkT'+str(tauN)], WEIGHT )
                                getattr( self, ('fakereco' if isfakeJet else 'reco')+iJ+'_tau_0p5_'+str(tauN)+'_OP_kT'+sysUnc+iSel ).Fill( ireco['0p5OPkT'+str(tauN)], WEIGHT )
                                getattr( self, ('fakereco' if isfakeJet else 'reco')+iJ+'_tau_1_'+str(tauN)+'_OP_kT'+sysUnc+iSel ).Fill( ireco['1OPkT'+str(tauN)], WEIGHT )
                                getattr( self, ('fakereco' if isfakeJet else 'reco')+iJ+'_tau_2_'+str(tauN)+'_OP_kT'+sysUnc+iSel ).Fill( ireco['2OPkT'+str(tauN)], WEIGHT )


                        if self.addSDJets and ireco['sdjet']:

                            if sysUnc.startswith('_nom'):
                                getattr( self, 'recoSD'+iJ+'Pt'+sysUnc+iSel ).Fill( ireco['sdjet'].perp(), WEIGHT )
                                getattr( self, 'recoSD'+iJ+'SDmass'+sysUnc+iSel ).Fill( ireco['sdjet'].m(), WEIGHT )
                                getattr( self, 'recoSD'+iJ+'Eta'+sysUnc+iSel ).Fill( ireco['sdjet'].eta(), WEIGHT )
                                getattr( self, 'recoSD'+iJ+'Tau21'+sysUnc+iSel ).Fill( ireco['sdtau21'], WEIGHT )
                                getattr( self, 'recoSD'+iJ+'Tau32'+sysUnc+iSel ).Fill( ireco['sdtau32'], WEIGHT )

                            for tauN in range(1, self.maxTau+1):
                                getattr( self, 'recoSD'+iJ+'_tau_0p5_'+str(tauN)+sysUnc+iSel ).Fill( ireco['sd0p5'+str(tauN)], WEIGHT )
                                getattr( self, 'recoSD'+iJ+'_tau_1_'+str(tauN)+sysUnc+iSel ).Fill( ireco['sd1'+str(tauN)], WEIGHT )
                                getattr( self, 'recoSD'+iJ+'_tau_2_'+str(tauN)+sysUnc+iSel ).Fill( ireco['sd2'+str(tauN)], WEIGHT )
                                if self.addMoreSchemes:
                                    getattr( self, 'recoSD'+iJ+'_tau_0p5_'+str(tauN)+'_WTA_kT'+sysUnc+iSel ).Fill( ireco['sd0p5WTAkT'+str(tauN)], WEIGHT )
                                    getattr( self, 'recoSD'+iJ+'_tau_1_'+str(tauN)+'_WTA_kT'+sysUnc+iSel ).Fill( ireco['sd1WTAkT'+str(tauN)], WEIGHT )
                                    getattr( self, 'recoSD'+iJ+'_tau_2_'+str(tauN)+'_WTA_kT'+sysUnc+iSel ).Fill( ireco['sd2WTAkT'+str(tauN)], WEIGHT )
                                    getattr( self, 'recoSD'+iJ+'_tau_0p5_'+str(tauN)+'_OP_kT'+sysUnc+iSel ).Fill( ireco['sd0p5OPkT'+str(tauN)], WEIGHT )
                                    getattr( self, 'recoSD'+iJ+'_tau_1_'+str(tauN)+'_OP_kT'+sysUnc+iSel ).Fill( ireco['sd1OPkT'+str(tauN)], WEIGHT )
                                    getattr( self, 'recoSD'+iJ+'_tau_2_'+str(tauN)+'_OP_kT'+sysUnc+iSel ).Fill( ireco['sd2OPkT'+str(tauN)], WEIGHT )


                        #### FIlling response matrices
                        if self.isMC and not isfakeJet:
                            for q, igen in genAK8jet.iteritems():
                                if sysUnc.endswith('nom'):
                                    getattr( self, 'resol'+iJ+'Pt'+iSel ).Fill( getattr(ireco['jet'], 'pt')/getattr(igen['jet'], 'pt'), weight )
                                    getattr( self, 'resol'+iJ+'SDmass'+iSel ).Fill( getattr(ireco['jet'], 'msoftdrop')/getattr(igen['jet'], 'mass'), weight )
                                    getattr( self, 'resol'+iJ+'Tau21'+iSel ).Fill( ireco['tau21']/igen['tau21'], weight )
                                    getattr( self, 'resol'+iJ+'Tau32'+iSel ).Fill( ireco['tau32']/igen['tau32'], weight )

                                getattr( self, 'resp'+iJ+'Tau21'+sysUnc+iSel ).Fill( igen['tau21'], ireco['tau21'], WEIGHT )
                                getattr( self, 'resp'+iJ+'Tau32'+sysUnc+iSel ).Fill( igen['tau32'], ireco['tau32'], WEIGHT )
                                if self.addSDJets:
                                    getattr( self, 'respSD'+iJ+'Tau32'+sysUnc+iSel ).Fill( igen['sdtau32'], ireco['sdtau32'], WEIGHT )
                                    getattr( self, 'respSD'+iJ+'Tau21'+sysUnc+iSel ).Fill( igen['sdtau21'], ireco['sdtau21'], WEIGHT )

                                for tauN in range(1, self.maxTau+1):
                                    getattr( self, 'resp'+iJ+'_tau_0p5_'+str(tauN)+sysUnc+iSel ).Fill( igen['0p5'+str(tauN)], ireco['0p5'+str(tauN)], WEIGHT )
                                    getattr( self, 'resp'+iJ+'_tau_1_'+str(tauN)+sysUnc+iSel ).Fill( igen['1'+str(tauN)], ireco['1'+str(tauN)], WEIGHT )
                                    getattr( self, 'resp'+iJ+'_tau_2_'+str(tauN)+sysUnc+iSel ).Fill( igen['2'+str(tauN)], ireco['2'+str(tauN)], WEIGHT )
                                    if sysUnc.endswith('nom'):
                                        getattr( self, 'resol'+iJ+'_tau_0p5_'+str(tauN)+iSel ).Fill( ireco['0p5'+str(tauN)]/igen['0p5'+str(tauN)], WEIGHT )
                                        getattr( self, 'resol'+iJ+'_tau_1_'+str(tauN)+iSel ).Fill( ireco['1'+str(tauN)]/igen['1'+str(tauN)], WEIGHT )
                                        getattr( self, 'resol'+iJ+'_tau_2_'+str(tauN)+iSel ).Fill( ireco['2'+str(tauN)]/igen['2'+str(tauN)], WEIGHT )
                                    if self.addMoreSchemes:
                                        getattr( self, 'resp'+iJ+'_tau_0p5_'+str(tauN)+'_WTA_kT'+sysUnc+iSel ).Fill( igen['0p5WTAkT'+str(tauN)], ireco['0p5WTAkT'+str(tauN)], WEIGHT )
                                        getattr( self, 'resp'+iJ+'_tau_1_'+str(tauN)+'_WTA_kT'+sysUnc+iSel ).Fill( igen['1WTAkT'+str(tauN)], ireco['1WTAkT'+str(tauN)], WEIGHT )
                                        getattr( self, 'resp'+iJ+'_tau_2_'+str(tauN)+'_WTA_kT'+sysUnc+iSel ).Fill( igen['2WTAkT'+str(tauN)], ireco['2WTAkT'+str(tauN)], WEIGHT )
                                        getattr( self, 'resp'+iJ+'_tau_0p5_'+str(tauN)+'_OP_kT'+sysUnc+iSel ).Fill( igen['0p5OPkT'+str(tauN)], ireco['0p5OPkT'+str(tauN)], WEIGHT )
                                        getattr( self, 'resp'+iJ+'_tau_1_'+str(tauN)+'_OP_kT'+sysUnc+iSel ).Fill( igen['1OPkT'+str(tauN)], ireco['1OPkT'+str(tauN)], WEIGHT )
                                        getattr( self, 'resp'+iJ+'_tau_2_'+str(tauN)+'_OP_kT'+sysUnc+iSel ).Fill( igen['2OPkT'+str(tauN)], ireco['2OPkT'+str(tauN)], WEIGHT )

                                    if self.addSDJets:
                                        getattr( self, 'respSD'+iJ+'_tau_0p5_'+str(tauN)+sysUnc+iSel ).Fill( igen['sd0p5'+str(tauN)], ireco['sd0p5'+str(tauN)], WEIGHT )
                                        getattr( self, 'respSD'+iJ+'_tau_1_'+str(tauN)+sysUnc+iSel ).Fill( igen['sd1'+str(tauN)], ireco['sd1'+str(tauN)], WEIGHT )
                                        getattr( self, 'respSD'+iJ+'_tau_2_'+str(tauN)+sysUnc+iSel ).Fill( igen['sd2'+str(tauN)], ireco['sd2'+str(tauN)], WEIGHT )
                                        if self.addMoreSchemes:
                                            getattr( self, 'respSD'+iJ+'_tau_0p5_'+str(tauN)+'_WTA_kT'+sysUnc+iSel ).Fill( igen['sd0p5WTAkT'+str(tauN)], ireco['sd0p5WTAkT'+str(tauN)], WEIGHT )
                                            getattr( self, 'respSD'+iJ+'_tau_1_'+str(tauN)+'_WTA_kT'+sysUnc+iSel ).Fill( igen['sd1WTAkT'+str(tauN)], ireco['sd1WTAkT'+str(tauN)], WEIGHT )
                                            getattr( self, 'respSD'+iJ+'_tau_2_'+str(tauN)+'_WTA_kT'+sysUnc+iSel ).Fill( igen['sd2WTAkT'+str(tauN)], ireco['sd2WTAkT'+str(tauN)], WEIGHT )
                                            getattr( self, 'respSD'+iJ+'_tau_0p5_'+str(tauN)+'_OP_kT'+sysUnc+iSel ).Fill( igen['sd0p5OPkT'+str(tauN)], ireco['sd0p5OPkT'+str(tauN)], WEIGHT )
                                            getattr( self, 'respSD'+iJ+'_tau_1_'+str(tauN)+'_OP_kT'+sysUnc+iSel ).Fill( igen['sd1OPkT'+str(tauN)], ireco['sd1OPkT'+str(tauN)], WEIGHT )
                                            getattr( self, 'respSD'+iJ+'_tau_2_'+str(tauN)+'_OP_kT'+sysUnc+iSel ).Fill( igen['sd2OPkT'+str(tauN)], ireco['sd2OPkT'+str(tauN)], WEIGHT )

        else:
            recoAK8jetInfo = {}
            for iJ, igen in genAK8jet.iteritems():
                if ('iSel' in igen):
                    getattr( self, 'cat'+igen['iSel'] ).Fill( 2 )
                    getattr( self, 'missgen'+iJ+'Mass'+igen['iSel'] ).Fill( igen['jet'].mass, weight )
                    getattr( self, 'missgen'+iJ+'Pt'+igen['iSel'] ).Fill( igen['jet'].pt, weight )
                    getattr( self, 'missgen'+iJ+'Eta'+igen['iSel'] ).Fill( igen['jet'].eta, weight )
                    getattr( self, 'missgen'+iJ+'Tau21'+igen['iSel'] ).Fill( igen['tau21'], weight )
                    getattr( self, 'missgen'+iJ+'Tau32'+igen['iSel'] ).Fill( igen['tau32'], weight )
                    for tauN in range(1, self.maxTau+1):
                        getattr( self, 'missgen'+iJ+'_tau_0p5_'+str(tauN)+igen['iSel'] ).Fill( igen['0p5'+str(tauN)], weight )
                        getattr( self, 'missgen'+iJ+'_tau_1_'+str(tauN)+igen['iSel'] ).Fill( igen['1'+str(tauN)], weight )
                        getattr( self, 'missgen'+iJ+'_tau_2_'+str(tauN)+igen['iSel'] ).Fill( igen['2'+str(tauN)], weight )
                        if self.addMoreSchemes:
                            getattr( self, 'missgen'+iJ+'_tau_0p5_'+str(tauN)+'_WTA_kT'+igen['iSel'] ).Fill( igen['0p5WTAkT'+str(tauN)], weight )
                            getattr( self, 'missgen'+iJ+'_tau_1_'+str(tauN)+'_WTA_kT'+igen['iSel'] ).Fill( igen['1WTAkT'+str(tauN)], weight )
                            getattr( self, 'missgen'+iJ+'_tau_2_'+str(tauN)+'_WTA_kT'+igen['iSel'] ).Fill( igen['2WTAkT'+str(tauN)], weight )
                            getattr( self, 'missgen'+iJ+'_tau_0p5_'+str(tauN)+'_OP_kT'+igen['iSel'] ).Fill( igen['0p5OPkT'+str(tauN)], weight )
                            getattr( self, 'missgen'+iJ+'_tau_1_'+str(tauN)+'_OP_kT'+igen['iSel'] ).Fill( igen['1OPkT'+str(tauN)], weight )
                            getattr( self, 'missgen'+iJ+'_tau_2_'+str(tauN)+'_OP_kT'+igen['iSel'] ).Fill( igen['2OPkT'+str(tauN)], weight )
                else:
                    getattr( self, 'cat'+iSel ).Fill( 4 )

        return recoAK8jetInfo

    #############################################################################
    def genSelection( self, event ):
        '''Analyzing reco information'''

        genJetsAK8 = list(Collection( event, 'GenJetAK8' ))
        genLeptons = list(Collection( event, 'GenDressedLepton' ))
        genJets = list(Collection( event, 'GenJet'))
        genParticles = Collection(event, 'GenPart')
        genmet = Object( event, 'GenMET')

        ### Lepton selection
        genElectrons  = [x for x in genLeptons if abs(x.pdgId)==11 and x.pt>self.minElectronPt and abs(x.eta)<self.maxMuonEta ]
        genElectrons.sort(key=lambda x:x.pt, reverse=True)

        genMuons = [ x for x in genLeptons if abs(x.pdgId)==13 and  x.pt > self.minMuonPt and abs(x.eta) < self.maxMuonEta ]
        genMuons.sort(key=lambda x:x.pt, reverse=True)
        ##################################################

        #### MET (not sure if needed)
        genMET = ROOT.TLorentzVector()
        genMET.SetPtEtaPhiE(genmet.pt, 0., genmet.phi, 0)
        ##################################################

        #### Basic AK8 jet selection
        genAK8jets = [ x for x in genJetsAK8 if x.pt > self.minAK8JetPt and abs(x.eta) < self.maxJetAK8Eta ]
        genAK8HT = sum( [ x.pt for x in genAK8jets ] )
        genAK8jets.sort(key=lambda x:x.pt,reverse=True)
        ##################################################

        #### Basic AK4 bjet selection
        genAK4bjets = [ x for x in genJets if x.pt > self.minJetPt and abs(x.eta) < self.maxJetEta and abs(x.hadronFlavour)==5 ]
        genAK4bjets.sort(key=lambda x:x.pt,reverse=True)
        ##################################################

        #### Weight
        weight = event.genWeight

        #### Checking no selection
        getattr( self, 'ngenleps_noSel' ).Fill( len(genMuons)+len(genElectrons), weight )
        for imuon in genMuons:
            getattr( self, 'genmuons_pt_noSel' ).Fill( imuon.pt, weight )
            getattr( self, 'genmuons_eta_noSel' ).Fill( imuon.eta, weight )
            getattr( self, 'genmuons_phi_noSel' ).Fill( imuon.phi, weight )
        for iele in genElectrons:
            getattr( self, 'geneles_pt_noSel' ).Fill( iele.pt, weight )
            getattr( self, 'geneles_eta_noSel' ).Fill( iele.eta, weight )
            getattr( self, 'geneles_phi_noSel' ).Fill( iele.phi, weight )
        getattr( self, 'ngenAK8jets_noSel' ).Fill( len(genAK8jets), weight )
        getattr( self, 'genHT_noSel' ).Fill( genAK8HT, weight )
        for ijet in genAK8jets:
            getattr( self, 'AK8genjets_pt_noSel' ).Fill( ijet.pt, weight )
            getattr( self, 'AK8genjets_eta_noSel' ).Fill( ijet.eta, weight )
            getattr( self, 'AK8genjets_phi_noSel' ).Fill( ijet.phi, weight )
            getattr( self, 'AK8genjets_mass_noSel' ).Fill( ijet.mass, weight )
        getattr( self, 'ngenAK4jets_noSel' ).Fill( len(genAK4bjets), weight )
        for ijet in genAK4bjets:
            getattr( self, 'AK4genjets_pt_noSel' ).Fill( ijet.pt, weight )
            getattr( self, 'AK4genjets_eta_noSel' ).Fill( ijet.eta, weight )
            getattr( self, 'AK4genjets_phi_noSel' ).Fill( ijet.phi, weight )
        getattr( self, 'genMETPt_noSel' ).Fill( genMET.Pt(), weight )
        ptAsym = ( genAK8jets[0].pt - genAK8jets[1].pt ) / (genAK8jets[0].pt + genAK8jets[1].pt) if len(genAK8jets)>1 else 0
        deltaPhi = genAK8jets[0].p4().DeltaPhi( genAK8jets[1].p4() ) if len(genAK8jets)>1 else 0
        getattr( self, 'genPtAsym_noSel' ).Fill( ptAsym, weight )
        getattr( self, 'genDeltaPhi_noSel' ).Fill( deltaPhi, weight )

        ##### Applying selection
        #### Creating Nsub basis, filling histos and creating branches IF iSel
        iSel = None
        genAK8jetInfo = {}
        getattr( self, 'cutflow_gen' ).Fill( 0 )
        getattr( self, 'cutflowWeight_gen' ).Fill( 0, weight )

        if self.selection.startswith('dijet'):

            if (len(genMuons)+len(genElectrons)==0) and (len(genAK8jets)>1) and (ptAsym<0.3) and (deltaPhi>2) and (genAK8jets[1].pt>self.minLeadAK8JetPtDijet):
                iSel = '_dijetSel'
                if self.createTrees: self.out.fillBranch( 'goodgenjet0_Sel', 2 )
                getattr( self, 'cutflow_gen' ).Fill( 2 )
                getattr( self, 'cutflowWeight_gen' ).Fill( 2, weight )
                tmpJet1 = genAK8jets[0] if abs(genAK8jets[0].eta) > abs(genAK8jets[1].eta) else genAK8jets[1]
                tmpJet2 = genAK8jets[1] if abs(genAK8jets[0].eta) > abs(genAK8jets[1].eta) else genAK8jets[0]
                genAK8jetInfo['Jet1'] = self.createNsubBasis( iSel, tmpJet1, self.minLeadAK8JetPtDijet, event, 'GenPartAK8' )
                genAK8jetInfo['Jet2'] = self.createNsubBasis( iSel, tmpJet2, self.minLeadAK8JetPtDijet, event, 'GenPartAK8' )

            else:
                if self.createTrees: self.out.fillBranch( 'goodgenjet0_Sel', 0 )

        elif self.selection.startswith('Wtop'):

            if (len(genMuons)==1) and (len(genAK8jets)>0) and (len(genAK4bjets)>1) and (genMET.Pt()>self.METCutWtop):

                ### removing ak4 jets inside leadAK8 jet
                for bjet in genAK4bjets:
                    if genAK8jets[0].p4().DeltaR( bjet.p4() )<0.8 : genAK4bjets.remove(bjet)

                ### defining muon isolation and leptonic top
                muonIso = []
                leptonicTop = []
                for bjet in genAK4bjets:
                    if bjet.p4().DeltaR( genMuons[0].p4() )<0.4: muonIso.append( False )
                    if (genMuons[0].p4().DeltaR( bjet.p4() )>0.4) and (genMuons[0].p4().DeltaR( bjet.p4() )<1.5): leptonicTop.append( True )

                if all(muonIso) and ((genMET+genMuons[0].p4()).Pt()>200) and any(leptonicTop) and (genAK8jets[0].p4().DeltaR(genMuons[0].p4())>0.8) and (len(genAK4bjets)>1):

                    if (genAK8jets[0].mass<self.maxSDMassW) and (genAK8jets[0].mass>self.minSDMassW) and (genAK8jets[0].pt>self.minLeadAK8JetPtW):
                        iSel = '_WSel'
                        if self.createTrees: self.out.fillBranch( 'goodgenjet0_Sel', 4 )
                        getattr( self, 'cutflow_gen' ).Fill( 4 )
                        getattr( self, 'cutflowWeight_gen' ).Fill( 4, weight )
                        genAK8jetInfo['Jet'] = self.createNsubBasis( iSel, genAK8jets[0], self.minLeadAK8JetPtW, event, 'GenPartAK8' )

                    elif (genAK8jets[0].mass>self.minSDMassTop) and (genAK8jets[0].pt>self.minLeadAK8JetPtTop):
                        iSel = '_topSel'
                        if self.createTrees: self.out.fillBranch( 'goodgenjet0_Sel', 6 )
                        getattr( self, 'cutflow_gen' ).Fill( 6 )
                        getattr( self, 'cutflowWeight_gen' ).Fill( 6, weight )
                        genAK8jetInfo['Jet'] = self.createNsubBasis( iSel, genAK8jets[0], self.minLeadAK8JetPtTop, event, 'GenPartAK8' )

                    else:
                        if self.createTrees: self.out.fillBranch( 'goodgenjet0_Sel', 8 )
                        getattr( self, 'cutflow_gen' ).Fill( 8 )
                        getattr( self, 'cutflowWeight_gen' ).Fill( 8, weight )
            else:
                if self.createTrees: self.out.fillBranch( 'goodgenjet0_Sel', 0 )

        ##### Filling histograms
        if iSel:

            #### Checking nominal selection with weights
            getattr( self, 'ngenleps'+iSel ).Fill( len(genMuons)+len(genElectrons), weight )
            for imuon in genMuons:
                getattr( self, 'genmuons_pt'+iSel ).Fill( imuon.pt, weight )
                getattr( self, 'genmuons_eta'+iSel ).Fill( imuon.eta, weight )
                getattr( self, 'genmuons_phi'+iSel ).Fill( imuon.phi, weight )
            for iele in genElectrons:
                getattr( self, 'geneles_pt'+iSel ).Fill( iele.pt, weight )
                getattr( self, 'geneles_eta'+iSel ).Fill( iele.eta, weight )
                getattr( self, 'geneles_phi'+iSel ).Fill( iele.phi, weight )
            getattr( self, 'ngenAK8jets'+iSel ).Fill( len(genAK8jets), weight )
            getattr( self, 'genHT'+iSel ).Fill( genAK8HT, weight )
            for ijet in genAK8jets:
                getattr( self, 'AK8genjets_pt'+iSel ).Fill( ijet.pt, weight )
                getattr( self, 'AK8genjets_eta'+iSel ).Fill( ijet.eta, weight )
                getattr( self, 'AK8genjets_phi'+iSel ).Fill( ijet.phi, weight )
                getattr( self, 'AK8genjets_mass'+iSel ).Fill( ijet.mass, weight )
            getattr( self, 'ngenAK4jets'+iSel ).Fill( len(genAK4bjets), weight )
            for ijet in genAK4bjets:
                getattr( self, 'AK4genjets_pt'+iSel ).Fill( ijet.pt, weight )
                getattr( self, 'AK4genjets_eta'+iSel ).Fill( ijet.eta, weight )
                getattr( self, 'AK4genjets_phi'+iSel ).Fill( ijet.phi, weight )
            getattr( self, 'genMETPt'+iSel ).Fill( genMET.Pt(), weight )
            getattr( self, 'genPtAsym'+iSel ).Fill( ptAsym, weight )
            getattr( self, 'genDeltaPhi'+iSel ).Fill( deltaPhi, weight )

            for iJ, igen in genAK8jetInfo.iteritems():
                getattr( self, 'gen'+iJ+'_pt'+iSel ).Fill( igen['jet'].pt, weight )
                getattr( self, 'gen'+iJ+'_eta'+iSel ).Fill( igen['jet'].eta, weight )
                getattr( self, 'gen'+iJ+'_phi'+iSel ).Fill( igen['jet'].phi, weight )
                getattr( self, 'gen'+iJ+'_mass'+iSel ).Fill( igen['jet'].mass, weight )

                getattr( self, 'gen'+iJ+'Tau21'+iSel ).Fill( igen['tau21'], weight )
                getattr( self, 'gen'+iJ+'Tau32'+iSel ).Fill( igen['tau32'], weight )
                for tauN in range(1, self.maxTau+1):
                    getattr( self, 'gen'+iJ+'_tau_0p5_'+str(tauN)+iSel ).Fill( igen['0p5'+str(tauN)], weight )
                    getattr( self, 'gen'+iJ+'_tau_1_'+str(tauN)+iSel ).Fill( igen['1'+str(tauN)], weight )
                    getattr( self, 'gen'+iJ+'_tau_2_'+str(tauN)+iSel ).Fill( igen['2'+str(tauN)], weight )
                    if self.addMoreSchemes:
                        getattr( self, 'gen'+iJ+'_tau_0p5_'+str(tauN)+'_WTA_kT'+iSel ).Fill( igen['0p5WTAkT'+str(tauN)], weight )
                        getattr( self, 'gen'+iJ+'_tau_1_'+str(tauN)+'_WTA_kT'+iSel ).Fill( igen['1WTAkT'+str(tauN)], weight )
                        getattr( self, 'gen'+iJ+'_tau_2_'+str(tauN)+'_WTA_kT'+iSel ).Fill( igen['2WTAkT'+str(tauN)], weight )
                        getattr( self, 'gen'+iJ+'_tau_0p5_'+str(tauN)+'_OP_kT'+iSel ).Fill( igen['0p5OPkT'+str(tauN)], weight )
                        getattr( self, 'gen'+iJ+'_tau_1_'+str(tauN)+'_OP_kT'+iSel ).Fill( igen['1OPkT'+str(tauN)], weight )
                        getattr( self, 'gen'+iJ+'_tau_2_'+str(tauN)+'_OP_kT'+iSel ).Fill( igen['2OPkT'+str(tauN)], weight )

                if self.addSDJets and igen['sdjet']:

                    getattr( self, 'genSD'+iJ+'Pt'+iSel ).Fill( igen['sdjet'].perp(), weight )
                    getattr( self, 'genSD'+iJ+'SDmass'+iSel ).Fill( igen['sdjet'].m(), weight )
                    getattr( self, 'genSD'+iJ+'Eta'+iSel ).Fill( igen['sdjet'].eta(), weight )
                    getattr( self, 'genSD'+iJ+'Tau21'+iSel ).Fill( igen['sdtau21'], weight )
                    getattr( self, 'genSD'+iJ+'Tau32'+iSel ).Fill( igen['sdtau32'], weight )

                    for tauN in range(1, self.maxTau+1):
                        getattr( self, 'genSD'+iJ+'_tau_0p5_'+str(tauN)+iSel ).Fill( igen['sd0p5'+str(tauN)], weight )
                        getattr( self, 'genSD'+iJ+'_tau_1_'+str(tauN)+iSel ).Fill( igen['sd1'+str(tauN)], weight )
                        getattr( self, 'genSD'+iJ+'_tau_2_'+str(tauN)+iSel ).Fill( igen['sd2'+str(tauN)], weight )
                        if self.addMoreSchemes:
                            getattr( self, 'genSD'+iJ+'_tau_0p5_'+str(tauN)+'_WTA_kT'+iSel ).Fill( igen['sd0p5WTAkT'+str(tauN)], weight )
                            getattr( self, 'genSD'+iJ+'_tau_1_'+str(tauN)+'_WTA_kT'+iSel ).Fill( igen['sd1WTAkT'+str(tauN)], weight )
                            getattr( self, 'genSD'+iJ+'_tau_2_'+str(tauN)+'_WTA_kT'+iSel ).Fill( igen['sd2WTAkT'+str(tauN)], weight )
                            getattr( self, 'genSD'+iJ+'_tau_0p5_'+str(tauN)+'_OP_kT'+iSel ).Fill( igen['sd0p5OPkT'+str(tauN)], weight )
                            getattr( self, 'genSD'+iJ+'_tau_1_'+str(tauN)+'_OP_kT'+iSel ).Fill( igen['sd1OPkT'+str(tauN)], weight )
                            getattr( self, 'genSD'+iJ+'_tau_2_'+str(tauN)+'_OP_kT'+iSel ).Fill( igen['sd2OPkT'+str(tauN)], weight )

        return genAK8jetInfo


    #############################################################################
    def createNsubBasis(self, iSel, AK8jet, minLeadAK8JetPt, event, PFCollection):
        '''Generic, taking a AK8 jet and computing Nsub basis from PFCollection'''

        pfCands = list(Collection(event, PFCollection))
        ak8jet = {}          ### Storing good jet as list for later use

        ##### Computing quantities
        if (AK8jet.pt > minLeadAK8JetPt*0.8):    #### store jets in the range of the pt selection
            ak8jet['jet'] = AK8jet
            ak8jet['iSel'] = iSel

            #### Run calculations of NSub bases and store for ungroomed AK8jets (default in CMS)

            #### Applying PUPPI weights to the PF candidates
            constituents = ROOT.vector("TLorentzVector")()
            CandsPUPPIweightedVec = ROOT.vector("TLorentzVector")()
            for p in pfCands :
                tp = ROOT.TLorentzVector(p.p4().Px(), p.p4().Py(), p.p4().Pz(), p.p4().E())
                try: tp = tp * p.puppiWeight
                except RuntimeError: tp = tp    ### for genjets
                CandsPUPPIweightedVec.push_back(tp)

            #### Storing only the PF candidates that are close to the leadAK8jet (constituents)
            for x in CandsPUPPIweightedVec:
                if abs(AK8jet.p4().DeltaR( x )) < 0.8: constituents.push_back(x)

            #### Computing n-subjetiness basis from PF PUPPI constituents
            nsub0p5 = self.nSub0p5.getTau( self.maxTau, constituents )
            nsub1 = self.nSub1.getTau( self.maxTau, constituents )
            nsub2 = self.nSub2.getTau( self.maxTau, constituents )
            nsub1_OP_kT = self.nSub1_OP_kT.getTau( 3, constituents )    ### needed for genjet tau21 tau32

            if self.addMoreSchemes:
                nsub0p5_WTA_kT = self.nSub0p5_WTA_kT.getTau( self.maxTau, constituents )
                nsub1_WTA_kT = self.nSub1_WTA_kT.getTau( self.maxTau, constituents )
                nsub2_WTA_kT = self.nSub2_WTA_kT.getTau( self.maxTau, constituents )

                nsub0p5_OP_kT = self.nSub0p5_OP_kT.getTau( self.maxTau, constituents )
                nsub1_OP_kT = self.nSub1_OP_kT.getTau( self.maxTau, constituents )
                nsub2_OP_kT = self.nSub2_OP_kT.getTau( self.maxTau, constituents )

            ### default in CMS OP_KT https://github.com/cms-sw/cmssw/blob/9834f5dc9ff342ddef08b73d6c294cad36575772/RecoJets/JetProducers/python/nJettinessAdder_cfi.py
            try: ak8jet['tau21'] = nsub1_OP_kT[1]/nsub1_OP_kT[0]
            except ZeroDivisionError: ak8jet['tau21'] = -1
            try: ak8jet['tau32'] = nsub1_OP_kT[2]/nsub1_OP_kT[1]
            except ZeroDivisionError: ak8jet['tau32'] = -1


            #### filling histos and branches with nsub basis
            for tauN in range(self.maxTau):
                ak8jet['0p5'+str(tauN+1)] = nsub0p5[tauN]
                ak8jet['1'+str(tauN+1)] = nsub1[tauN]
                ak8jet['2'+str(tauN+1)] = nsub2[tauN]

                if self.addMoreSchemes:
                    ak8jet['0p5WTAkT'+str(tauN+1)] = nsub0p5_WTA_kT[tauN]
                    ak8jet['1WTAkT'+str(tauN+1)] = nsub1_WTA_kT[tauN]
                    ak8jet['2WTAkT'+str(tauN+1)] = nsub2_WTA_kT[tauN]

                    ak8jet['0p5OPkT'+str(tauN+1)] = nsub0p5_OP_kT[tauN]
                    ak8jet['1OPkT'+str(tauN+1)] = nsub1_OP_kT[tauN]
                    ak8jet['2OPkT'+str(tauN+1)] = nsub2_OP_kT[tauN]
            ################################################## end of ungroomed jets

            ##################################################
            #### Run calculations of NSub bases and store for groomed AK8jets

            if self.addSDJets:
                #### Computing Softdrop jets
                sdAK8jets = self.sd.result( CandsPUPPIweightedVec )

                ### Storing good jet as list for later use
                if len(sdAK8jets)>0:

                    deltaR = 99999
                    sdIndex = -1
                    for isdInd, isdjet in enumerate(sdAK8jets):

                        #### Checking which jet is matched to the sdAK8jets
                        tmpisdjet = ROOT.TLorentzVector( )
                        tmpisdjet.SetPtEtaPhiM( isdjet.perp(), isdjet.eta(), isdjet.phi(), isdjet.m() )
                        tmpDeltaR = tmpisdjet.DeltaR( ak8jet['jet'].p4() )
                        if (tmpDeltaR < deltaR):
                            deltaR=tmpDeltaR
                            sdIndex= isdInd

                    ak8jet['sdjet'] = sdAK8jets[sdIndex]

                    # Cluster only the particles near the appropriate jet to save time
                    sd_constituents = ROOT.vector("TLorentzVector")()

                    for x in ak8jet['sdjet'].constituents():
                        sd_constits = ROOT.TLorentzVector( x.px(), x.py(), x.pz(), x.E())
                        if abs(ak8jet['sdjet'].delta_R( x )) < 0.8:
                            sd_constituents.push_back(sd_constits)
                    sd_nsub0p5 = self.nSub0p5.getTau( self.maxTau, sd_constituents )
                    sd_nsub1 = self.nSub1.getTau( self.maxTau, sd_constituents )
                    sd_nsub2 = self.nSub2.getTau( self.maxTau, sd_constituents )

                    if self.addMoreSchemes:
                        sd_nsub0p5_WTA_kT = self.nSub0p5_WTA_kT.getTau( self.maxTau, sd_constituents )
                        sd_nsub1_WTA_kT = self.nSub1_WTA_kT.getTau( self.maxTau, sd_constituents )
                        sd_nsub2_WTA_kT = self.nSub2_WTA_kT.getTau( self.maxTau, sd_constituents )

                        sd_nsub0p5_OP_kT = self.nSub0p5_OP_kT.getTau( self.maxTau, sd_constituents )
                        sd_nsub1_OP_kT = self.nSub1_OP_kT.getTau( self.maxTau, sd_constituents )
                        sd_nsub2_OP_kT = self.nSub2_OP_kT.getTau( self.maxTau, sd_constituents )


                    try: ak8jet['sdtau21'] = sd_nsub1_OP_kT[1]/sd_nsub1_OP_kT[0]
                    except ZeroDivisionError: ak8jet['sdtau21'] = -1
                    try: ak8jet['sdtau32'] = sd_nsub1_OP_kT[2]/sd_nsub1_OP_kT[1]
                    except ZeroDivisionError: ak8jet['sdtau32'] = -1

                    for tauN in range(self.maxTau):
                        ak8jet['sd0p5'+str(tauN+1)] = sd_nsub0p5[tauN]
                        ak8jet['sd1'+str(tauN+1)] = sd_nsub1[tauN]
                        ak8jet['sd2'+str(tauN+1)] = sd_nsub2[tauN]

                        if self.addMoreSchemes:
                            ak8jet['sd0p5WTAkT'+str(tauN+1)] = sd_nsub0p5_WTA_kT[tauN]
                            ak8jet['sd1WTAkT'+str(tauN+1)] = sd_nsub1_WTA_kT[tauN]
                            ak8jet['sd2WTAkT'+str(tauN+1)] = sd_nsub2_WTA_kT[tauN]

                            ak8jet['sd0p5OPkT'+str(tauN+1)] = sd_nsub0p5_OP_kT[tauN]
                            ak8jet['sd1OPkT'+str(tauN+1)] = sd_nsub1_OP_kT[tauN]
                            ak8jet['sd2OPkT'+str(tauN+1)] = sd_nsub2_OP_kT[tauN]

        return ak8jet


    #############################################################################
    def fillBranches( self, recoJet, genJet ):

        #### Filling branch with passAK8jet info after selection
        self.out.fillBranch("ngoodrecojet0", 1 )  ### dummy for nanoAOD Tools
        self.out.fillBranch("goodrecojet0_pt",  recoJet['jet'].pt_nom if recoJet else -9999 )
        self.out.fillBranch("goodrecojet0_eta",  recoJet['jet'].p4().Eta() if recoJet else -9999 )
        self.out.fillBranch("goodrecojet0_phi",  recoJet['jet'].p4().Phi() if recoJet else -9999 )
        self.out.fillBranch("goodrecojet0_mass",  recoJet['jet'].p4().M() if recoJet else -9999 )
        self.out.fillBranch("goodrecojet0_softdrop_mass", recoJet['jet'].msoftdrop_nom if recoJet else -9999 )
        self.out.fillBranch("goodrecojet0_pt_raw",  recoJet['jet'].pt_raw if recoJet else -9999 )
        self.out.fillBranch("goodrecojet0_mass_raw",  recoJet['jet'].mass_raw if recoJet else -9999 )
        self.out.fillBranch("goodrecojet0_tau21", recoJet['tau21'] if recoJet else -9999 )
        self.out.fillBranch("goodrecojet0_N21",  recoJet['jet'].n2b1 if recoJet else -9999 )
        self.out.fillBranch("goodrecojet0_corr_JEC",  recoJet['jet'].corr_JEC if recoJet else -9999 )
        self.out.fillBranch("goodrecojet0_corr_JER",  ( recoJet['jet'].corr_JER if (self.isMC and (recoJet)) else -99999 ) )
        self.out.fillBranch("goodrecojet0_corr_JMS",  ( recoJet['jet'].corr_JMS if (self.isMC and (recoJet)) else -99999 ) )
        self.out.fillBranch("goodrecojet0_corr_JMR",  ( recoJet['jet'].corr_JMR if (self.isMC and (recoJet)) else -99999 ) )
        self.out.fillBranch("goodrecojet0_mass_jmrUp",  ( recoJet['jet'].mass_jmrUp if (self.isMC and (recoJet)) else -99999 ) )
        self.out.fillBranch("goodrecojet0_mass_jmsUp",  ( recoJet['jet'].mass_jmsUp if (self.isMC and (recoJet)) else -99999 ) )
        self.out.fillBranch("goodrecojet0_mass_jmrDown",  ( recoJet['jet'].mass_jmrDown if (self.isMC and (recoJet)) else -99999 ) )
        self.out.fillBranch("goodrecojet0_mass_jmsDown",  ( recoJet['jet'].mass_jmsDown if (self.isMC and (recoJet)) else -99999 ) )
        for q in ['pt', 'mass']:
            for u in [ 'Up', 'Down' ]:
                self.out.fillBranch("goodrecojet0_"+q+'_jer'+u, ( getattr( recoJet['jet'], q+'_jer'+u ) if (self.isMC and (recoJet)) else -99999 ) )
                for jes in self.JESLabels:
                    self.out.fillBranch("goodrecojet0_"+q+'_jesUnc'+jes+u, ( getattr( recoJet['jet'], q+'_jes'+jes+u ) if (self.isMC and (recoJet)) else -99999 ) )

        for tauN in range(1, self.maxTau+1):
            self.out.fillBranch("goodrecojet0_tau_0p5_"+str(tauN),  recoJet['0p5'+str(tauN)] if recoJet else -99999  )
            self.out.fillBranch("goodrecojet0_tau_1_"+str(tauN),  recoJet['1'+str(tauN)] if recoJet else -99999  )
            self.out.fillBranch("goodrecojet0_tau_2_"+str(tauN),  recoJet['2'+str(tauN)] if recoJet else -99999  )

            if self.addMoreSchemes:
                self.out.fillBranch("goodrecojet0_tau_0p5_"+str(tauN)+'_WTA_kT',  recoJet['0p5WTAkT'+str(tauN)] if recoJet else -99999  )
                self.out.fillBranch("goodrecojet0_tau_1_"+str(tauN)+'_WTA_kT',  recoJet['1WTAkT'+str(tauN)] if recoJet else -99999  )
                self.out.fillBranch("goodrecojet0_tau_2_"+str(tauN)+'_WTA_kT',  recoJet['2WTAkT'+str(tauN)] if recoJet else -99999  )

                self.out.fillBranch("goodrecojet0_tau_0p5_"+str(tauN)+'_OP_kT',  recoJet['0p5OPkT'+str(tauN)] if recoJet else -99999  )
                self.out.fillBranch("goodrecojet0_tau_1_"+str(tauN)+'_OP_kT',  recoJet['1OPkT'+str(tauN)] if recoJet else -99999  )
                self.out.fillBranch("goodrecojet0_tau_2_"+str(tauN)+'_OP_kT',  recoJet['2OPkT'+str(tauN)] if recoJet else -99999  )

        self.out.fillBranch("nsd_goodrecojet0", 1 )  ## dummy
        self.out.fillBranch("sd_goodrecojet0_pt",  recoJet['sdjet'].perp() if recoJet else -9999 )
        self.out.fillBranch("sd_goodrecojet0_eta",  recoJet['sdjet'].eta() if recoJet else -9999 )
        self.out.fillBranch("sd_goodrecojet0_phi",  recoJet['sdjet'].phi() if recoJet else -9999 )
        self.out.fillBranch("sd_goodrecojet0_mass",  recoJet['sdjet'].m() if recoJet else -9999 )
        self.out.fillBranch("sd_goodrecojet0_tau21", recoJet['sdtau21'] if recoJet else -9999 )
        for tauN in range(1, self.maxTau+1):
            self.out.fillBranch("sd_goodrecojet0_tau_0p5_"+str(tauN),  recoJet['sd0p5'+str(tauN)] if recoJet else -99999  )
            self.out.fillBranch("sd_goodrecojet0_tau_1_"+str(tauN),  recoJet['sd1'+str(tauN)] if recoJet else -99999  )
            self.out.fillBranch("sd_goodrecojet0_tau_2_"+str(tauN),  recoJet['sd2'+str(tauN)] if recoJet else -99999  )

            if self.addMoreSchemes:
                self.out.fillBranch("sd_goodrecojet0_tau_0p5_"+str(tauN)+'_WTA_kT',  recoJet['sd0p5WTAkT'+str(tauN)] if recoJet else -99999  )
                self.out.fillBranch("sd_goodrecojet0_tau_1_"+str(tauN)+'_WTA_kT',  recoJet['sd1WTAkT'+str(tauN)] if recoJet else -99999  )
                self.out.fillBranch("sd_goodrecojet0_tau_2_"+str(tauN)+'_WTA_kT',  recoJet['sd2WTAkT'+str(tauN)] if recoJet else -99999  )

                self.out.fillBranch("sd_goodrecojet0_tau_0p5_"+str(tauN)+'_OP_kT',  recoJet['sd0p5OPkT'+str(tauN)] if recoJet else -99999  )
                self.out.fillBranch("sd_goodrecojet0_tau_1_"+str(tauN)+'_OP_kT',  recoJet['sd1OPkT'+str(tauN)] if recoJet else -99999  )
                self.out.fillBranch("sd_goodrecojet0_tau_2_"+str(tauN)+'_OP_kT',  recoJet['sd2OPkT'+str(tauN)] if recoJet else -99999  )

        self.out.fillBranch("ngoodgenjet0", 1 )  ## dummy
        self.out.fillBranch("goodgenjet0_pt",  genJet['jet'].pt if genJet else -9999 )
        self.out.fillBranch("goodgenjet0_eta",  genJet['jet'].p4().Eta() if genJet else -9999 )
        self.out.fillBranch("goodgenjet0_phi",  genJet['jet'].p4().Phi() if genJet else -9999 )
        self.out.fillBranch("goodgenjet0_mass",  genJet['jet'].p4().M() if genJet else -9999 )
        self.out.fillBranch("goodgenjet0_tau21", genJet['tau21'] if genJet else -9999 )
        self.out.fillBranch("nsd_goodgenjet0", 1 )  ## dummy
        self.out.fillBranch("sd_goodgenjet0_pt",  genJet['sdjet'].perp() if genJet else -9999 )
        self.out.fillBranch("sd_goodgenjet0_eta",  genJet['sdjet'].eta() if genJet else -9999 )
        self.out.fillBranch("sd_goodgenjet0_phi",  genJet['sdjet'].phi() if genJet else -9999 )
        self.out.fillBranch("sd_goodgenjet0_mass",  genJet['sdjet'].m() if genJet else -9999 )
        self.out.fillBranch("sd_goodgenjet0_tau21", genJet['sdtau21'] if genJet else -9999 )
        for tauN in range(1, self.maxTau+1):
            self.out.fillBranch("goodgenjet0_tau_0p5_"+str(tauN),  genJet['0p5'+str(tauN)] if genJet else -99999  )
            self.out.fillBranch("goodgenjet0_tau_1_"+str(tauN),  genJet['1'+str(tauN)] if genJet else -99999  )
            self.out.fillBranch("goodgenjet0_tau_2_"+str(tauN),  genJet['2'+str(tauN)] if genJet else -99999  )

            if self.addMoreSchemes:
                self.out.fillBranch("goodgenjet0_tau_0p5_"+str(tauN)+'_WTA_kT',  genJet['0p5WTAkT'+str(tauN)] if genJet else -99999  )
                self.out.fillBranch("goodgenjet0_tau_1_"+str(tauN)+'_WTA_kT',  genJet['1WTAkT'+str(tauN)] if genJet else -99999  )
                self.out.fillBranch("goodgenjet0_tau_2_"+str(tauN)+'_WTA_kT',  genJet['2WTAkT'+str(tauN)] if genJet else -99999  )

                self.out.fillBranch("goodgenjet0_tau_0p5_"+str(tauN)+'_OP_kT',  genJet['0p5OPkT'+str(tauN)] if genJet else -99999  )
                self.out.fillBranch("goodgenjet0_tau_1_"+str(tauN)+'_OP_kT',  genJet['1OPkT'+str(tauN)] if genJet else -99999  )
                self.out.fillBranch("goodgenjet0_tau_2_"+str(tauN)+'_OP_kT',  genJet['2OPkT'+str(tauN)] if genJet else -99999  )

            self.out.fillBranch("sd_goodgenjet0_tau_0p5_"+str(tauN),  genJet['sd0p5'+str(tauN)] if genJet else -99999  )
            self.out.fillBranch("sd_goodgenjet0_tau_1_"+str(tauN),  genJet['sd1'+str(tauN)] if genJet else -99999  )
            self.out.fillBranch("sd_goodgenjet0_tau_2_"+str(tauN),  genJet['sd2'+str(tauN)] if genJet else -99999  )

            if self.addMoreSchemes:
                self.out.fillBranch("sd_goodgenjet0_tau_0p5_"+str(tauN)+'_WTA_kT',  genJet['sd0p5WTAkT'+str(tauN)] if genJet else -99999  )
                self.out.fillBranch("sd_goodgenjet0_tau_1_"+str(tauN)+'_WTA_kT',  genJet['sd1WTAkT'+str(tauN)] if genJet else -99999  )
                self.out.fillBranch("sd_goodgenjet0_tau_2_"+str(tauN)+'_WTA_kT',  genJet['sd2WTAkT'+str(tauN)] if genJet else -99999  )

                self.out.fillBranch("sd_goodgenjet0_tau_0p5_"+str(tauN)+'_OP_kT',  genJet['sd0p5OPkT'+str(tauN)] if genJet else -99999  )
                self.out.fillBranch("sd_goodgenjet0_tau_1_"+str(tauN)+'_OP_kT',  genJet['sd1OPkT'+str(tauN)] if genJet else -99999  )
                self.out.fillBranch("sd_goodgenjet0_tau_2_"+str(tauN)+'_OP_kT',  genJet['sd2OPkT'+str(tauN)] if genJet else -99999  )

    #############################################################################
    def matchRecoGenParticle( self, event, recoJet ):

        genParticles = Collection(event, "GenPart")

        quarksFromW = GenQuarkFromW( genParticles )
        bquarksFromTop = GenBquarkFromTop( genParticles )
        allQuarksFromWtop = quarksFromW + bquarksFromTop

        listMatched = []
        for q in allQuarksFromWtop:
            #print event.event, q.pdgId, genParticles[q.genPartIdxMother].pdgId, q.p4().Pt()
            if recoJet.p4().DeltaR( q.p4() )<0.3: listMatched.append( True )
            else: listMatched.append( False )

        if (len(listMatched)==4) and all(listMatched[:2]) and not all(listMatched[2:]): boosted = 2  ## only boostedW
        elif (len(listMatched)==4) and all(listMatched[:2]) and any(listMatched[2:]): boosted = 4      ## boosted Top
        else: boosted = 0
        #print listMatched, boosted

        return boosted

    ##################### Helpful functions
    def printP4( self, c ):
        if hasattr( c, "p4"):
            s = ' %6.2f %5.2f %5.2f %6.2f ' % ( c.p4().Perp(), c.p4().Eta(), c.p4().Phi(), c.p4().M() )
        elif hasattr( c, "Perp"):
            s = ' %6.2f %5.2f %5.2f %6.2f ' % ( c.Perp(), c.Eta(), c.Phi(), c.M() )
        else:
            s = ' %6.2f %5.2f %5.2f %6.2f ' % ( c.perp(), c.eta(), c.phi(), c.m() )
        return s
    def printCollection(self,coll):
        for ic,c in enumerate(coll):
            s = self.printP4( c )
            print ' %3d : %s' % ( ic, s )

    def getSubjets(self, p4, subjets, dRmax=0.8):
        ret = []
        for subjet in subjets :
            if p4.DeltaR(subjet.p4()) < dRmax and len(ret) < 2 :
                ret.append(subjet.p4())
        return ret

###################### Different gen functions
def getDaughters(GenParticle,gp):
    ret = []
    tmpListGenParticles = list(GenParticle)
    for part in GenParticle:
        if part != gp:
            if part.genPartIdxMother == tmpListGenParticles.index(gp):
                ret.append(part)
    return ret

def GenBquarkFromTop(GenParticle):
    ret = []
    for gP in GenParticle:
        if (abs(gP.pdgId) == 5) and gP.genPartIdxMother>0:
            mom = GenParticle[gP.genPartIdxMother]
            if abs(mom.pdgId)  == 6:
                dauids = [abs(dau.pdgId) for dau in getDaughters(GenParticle,mom)]
                if 6 not in dauids:
                    ret.append(gP)
    return ret

def GenQuarkFromW(GenParticle):
    ret = []
    for gP in GenParticle:
        if gP.genPartIdxMother>0:
            if (abs(gP.pdgId) <= 5) and (abs(GenParticle[gP.genPartIdxMother].pdgId) == 24):
                ret.append(gP)
        if (abs(gP.pdgId) <= 5) and gP.genPartIdxMother>0:
            mom = GenParticle[gP.genPartIdxMother]
            if abs(mom.pdgId)  == 24:
                dauids = [abs(dau.pdgId) for dau in getDaughters(GenParticle,mom)]
                if 24 not in dauids:
                    ret.append(gP)
    return ret

