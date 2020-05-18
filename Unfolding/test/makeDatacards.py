#####################################
#####################################

#!/usr/bin/env python
import argparse, os, shutil, sys
from ROOT import *
import ROOT
from datasets import *
from array import array
import numpy as np
from collections import OrderedDict
from DrawHistogram import plotSimpleComparison
sys.path.insert(0,'../python/')
import CMS_lumi as CMS_lumi
import tdrstyle as tdrstyle

####gReset()
gROOT.SetBatch()
gROOT.ForceStyle()
tdrstyle.setTDRStyle()
gStyle.SetOptStat(0)

canvas={}

def createDatacards( dataFile, sigFiles, bkgFiles, variables, sel, sysUncert ):
    """docstring for createDataCards"""

    ### Getting input histos
    dataHistos = loadHistograms( dataFile, variables, sel, isMC=(False if args.process.startswith('data') else True) )
    signalHistos = loadHistograms( sigFiles, variables, sel, sysUnc=sysUncert )
    bkgHistos = loadHistograms( bkgFiles, variables, sel, sysUnc=sysUncert ) if args.process.startswith('data') else {}

    for ivar in variables:

        print '|------> Unfolding '+ivar

        ######## Cross check: plotting data vs all MC
        print '|------> Cross check: plotting data vs all MC'
        allBkgHisto = dataHistos['data_recoJet'+ivar+'_nom'+sel].Clone()
        allBkgHisto.Reset()
        if args.process.startswith('data'):
            for ibkg in bkgHistos:
                if ibkg.endswith('recoJet'+ivar+'_nom'+sel): allBkgHisto.Add( bkgHistos[ibkg].Clone() )
        allMCHisto = allBkgHisto.Clone()
        allMCHisto.Add( signalHistos[ next(iter(sigFiles))+'_recoJet'+ivar+'_nom'+sel ].Clone() )
        plotSimpleComparison( dataHistos['data_recoJet'+ivar+'_nom'+sel].Clone(), 'data', allMCHisto, 'allBkgs', ivar+'_from'+('Data' if args.process.startswith('data') else 'MC')+'_'+next(iter(sigFiles))+"_nom", 1, version=sel+'_MLU_'+args.version  )

        ######## Cross check: plotting response matrix
        tdrStyle.SetPadRightMargin(0.12)
        print '|------> Cross check: plotting response matrix for signal'
        can2D = TCanvas(ivar+'can2D', ivar+'can2D', 750, 500 )
        signalHistos[next(iter(sigFiles))+'_respJet'+ivar+'_nom'+sel].Draw("colz")
        can2D.SaveAs('Plots/'+ivar+'_from'+('Data' if args.process.startswith('data') else 'MC')+'_'+next(iter(sigFiles))+sel+'_responseMatrix'+args.version+'.png')




        textDict = OrderedDict()
        textDict['bin'] = [ 'bin' ]
        textDict['obs'] = [ 'observation' ]
        textDict['bin2'] = [ 'bin' ]
        textDict['proc'] = [ 'process' ]
        textDict['proc2'] = [ 'process' ]
        textDict['rate'] = [ 'rate' ]
        po = []

        for ibinReco in range(1, dataHistos['data_recoJet'+ivar+'_nom'+sel].GetNbinsX()+1 ):
            if dataHistos['data_recoJet'+ivar+'_nom'+sel].GetBinContent(ibinReco)<1: continue
            textDict['bin'].append('Reco_'+str(ibinReco))
            textDict['obs'].append( str( dataHistos['data_recoJet'+ivar+'_nom'+sel].GetBinContent(ibinReco) ) )
            po.append("--PO map='.*Gen_"+str(ibinReco)+':r_bin'+str(ibinReco)+"[1,-5,5]'")
            if args.process.startswith('data'):
                textDict['bin2'].append("Reco_"+str(ibinReco))    ### one for all Bkgs
                textDict['proc'].append("Bkg")  ## bkg
                textDict['proc2'].append("1")  ## bkg
                textDict['rate'].append(str(round(allBkgHisto.GetBinContent(ibinReco),2)))  ## bkg
            dummy=0
            for ibinGen in range(1, dataHistos['data_recoJet'+ivar+'_nom'+sel].GetNbinsX()+1 ):
                if signalHistos[next(iter(sigFiles))+'_respJet'+ivar+'_nom'+sel].GetBinContent(ibinGen,ibinReco)<.1: continue
                dummy=dummy+1
                textDict['bin2'].append("Reco_"+str(ibinReco))    ### one for ibinGen and one for ibinReco
                textDict['proc'].append("Gen_"+str(ibinGen))
                textDict['proc2'].append("-"+str(ibinGen))   ## 0 -1, -2 --> for signal
                textDict['rate'].append( str( round(signalHistos[next(iter(sigFiles))+'_respJet'+ivar+'_nom'+sel].GetBinContent(ibinGen,ibinReco),2)) )
            if(dummy==0):
                print 'removing rbin'+str(ibinReco)
                if not textDict['bin'][-1].startswith('bin'): textDict['bin'].pop()
                if not textDict['obs'][-1].startswith('observation'): textDict['obs'].pop()
                if not textDict['bin2'][-1].startswith('bin'): textDict['bin2'].pop()
                if not textDict['proc'][-1].startswith('process'): textDict['proc'].pop()
                if not textDict['proc2'][-1].startswith('process'): textDict['proc2'].pop()
                if not textDict['rate'][-1].startswith('rate'): textDict['rate'].pop()
                po.pop()

        ######## Creating datacard for combine
        datacardName = 'datacard_'+ivar+'_from'+('Data' if args.process.startswith('data') else 'MC')+'_'+next(iter(sigFiles))
        print '|------> Creating datacard: ', datacardName

        datacard = open( datacardName+'.txt', 'w')
        datacard.write("* imax\n")
        datacard.write("* jmax\n")
        datacard.write("* kmax\n")
        datacard.write("----------------\n")
        for x in textDict:
            datacard.write(' '.join(textDict[x])+'\n')

#        datacard.write("bin ")
#        for ibin in range(1, dataHistos['data_recoJet'+ivar+'_nom'+sel].GetNbinsX()+1 ):
#            if dataHistos['data_recoJet'+ivar+'_nom'+sel].GetBinContent(ibin)<1: continue  ### remove low stat bin
#            datacard.write("Reco_"+str(ibin)+" ")
#        datacard.write("\n")
#
#        datacard.write("observation ")
#        for ibin in range(1, dataHistos['data_recoJet'+ivar+'_nom'+sel].GetNbinsX()+1 ):
#            if dataHistos['data_recoJet'+ivar+'_nom'+sel].GetBinContent(ibin)<1: continue
#            datacard.write( str( dataHistos['data_recoJet'+ivar+'_nom'+sel].GetBinContent(ibin) )+" " )
#        datacard.write("\n")
#        datacard.write("----------------\n")
#
#        datacard.write("bin ")
#        for ibinReco in range(1, dataHistos['data_recoJet'+ivar+'_nom'+sel].GetNbinsX()+1 ):
#            if dataHistos['data_recoJet'+ivar+'_nom'+sel].GetBinContent(ibinReco)<1: continue
#            for ibinGen in range(1, dataHistos['data_recoJet'+ivar+'_nom'+sel].GetNbinsX()+1 ):
#                #if signalHistos[next(iter(sigFiles))+'_respJet'+ivar+'_nom'+sel].GetBinContent(ibinGen,ibinReco)<.1: continue
#                datacard.write("Reco_"+str(ibinReco)+' ')    ### one for ibinGen and one for ibinReco
#            if args.process.startswith('data'): datacard.write("Reco_"+str(ibinReco)+' ')    ### one for all Bkgs
#        datacard.write("\n")
#
#        datacard.write("process ")
#        for ibinReco in range(1, dataHistos['data_recoJet'+ivar+'_nom'+sel].GetNbinsX()+1 ):
#            if dataHistos['data_recoJet'+ivar+'_nom'+sel].GetBinContent(ibinReco)<1: continue
#            for ibinGen in range(1, dataHistos['data_recoJet'+ivar+'_nom'+sel].GetNbinsX()+1 ):
#                #if signalHistos[next(iter(sigFiles))+'_respJet'+ivar+'_nom'+sel].GetBinContent(ibinGen,ibinReco)<.1: continue
#                datacard.write("Gen_"+str(ibinGen)+' ')
#            if args.process.startswith('data'): datacard.write("Bkg ")  ## bkg
#        datacard.write("\n")
#
#        datacard.write("process ")
#        for ibinReco in range(1, dataHistos['data_recoJet'+ivar+'_nom'+sel].GetNbinsX()+1 ):
#            if dataHistos['data_recoJet'+ivar+'_nom'+sel].GetBinContent(ibinReco)<1: continue
#            for ibinGen in range(1, dataHistos['data_recoJet'+ivar+'_nom'+sel].GetNbinsX()+1 ):
#                #if signalHistos[next(iter(sigFiles))+'_respJet'+ivar+'_nom'+sel].GetBinContent(ibinGen,ibinReco)<.1:
#                #    print ibinGen, ibinReco, signalHistos[next(iter(sigFiles))+'_respJet'+ivar+'_nom'+sel].GetBinContent(ibinGen,ibinReco)
#                #    continue
#                datacard.write(" -"+str(ibinGen))   ## 0 -1, -2 --> for signal
#            if args.process.startswith('data'): datacard.write(" 1 ")                   ## bkg >0 for bkg
#        datacard.write("\n")
#
#        datacard.write("rate ")
#        for ibinReco in range(1, dataHistos['data_recoJet'+ivar+'_nom'+sel].GetNbinsX()+1 ):
#            if dataHistos['data_recoJet'+ivar+'_nom'+sel].GetBinContent(ibinReco)<1: continue
#            for ibinGen in range(1, dataHistos['data_recoJet'+ivar+'_nom'+sel].GetNbinsX()+1 ):
#                #if signalHistos[next(iter(sigFiles))+'_respJet'+ivar+'_nom'+sel].GetBinContent(ibinGen,ibinReco)<0.1: continue
#                datacard.write( str( round(signalHistos[next(iter(sigFiles))+'_respJet'+ivar+'_nom'+sel].GetBinContent(ibinGen,ibinReco),2))+" " )
#            if args.process.startswith('data'): datacard.write( str(round(allBkgHisto.GetBinContent(ibinReco),2))+' ' )
#        datacard.write("\n")
        datacard.write("----------------\n")

        #### Creating the combine command
        #po=' '.join(["--PO map='.*Gen_%d:r_bin%d[1,-20,20]'"%(ibinGen,ibinGen) for ibinGen in range(1, dataHistos['data_recoJet'+ivar+'_nom'+sel].GetNbinsX()+1) if dataHistos['data_recoJet'+ivar+'_nom'+sel].GetBinContent(ibinGen)>0 ])
        po = ' '.join(po)
        cmdText2Workspace = "text2workspace.py --X-allow-no-background "+datacardName+".txt -o "+datacardName+".root -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel "+po
        datacard.write("### RUN WITH COMMANDS: ####\n")
        datacard.write("# "+cmdText2Workspace+"\n")
        cmdCombine = 'combine -M MultiDimFit -d '+datacardName+'.root -t 0 -n '+ivar+'_from'+('Data' if args.process.startswith('data') else 'MC')+'_'+next(iter(sigFiles))
        #ro=','.join(["r_bin"+str(ibinGen)+"=1" for ibinGen in range(1, dataHistos['data_recoJet'+ivar+'_nom'+sel].GetNbinsX()+1) if dataHistos['data_recoJet'+ivar+'_nom'+sel].GetBinContent(ibinGen)>0 ])
        #cmdCombine = 'combine -M MultiDimFit '+datacardName+'.root -t -1 -n '+ivar+'_from'+('Data' if args.process.startswith('data') else 'MC')+'_'+next(iter(sigFiles))+' --setParameters='+ro
        #cmdCombine2 = 'combine -M MultiDimFit '+datacardName+'.root -t -1 -n '+ivar+'_from'+('Data' if args.process.startswith('data') else 'MC')+'_'+next(iter(sigFiles))+' --setParameters='+ro+' --algo=grid --points=100 -P r_bin1 --setParameterRanges r_bin1=0.5,1.5 --floatOtherPOIs=1'
        datacard.write("# Run with command: "+cmdCombine+" \n")
        datacard.write("############################\n")
        print '|------> To run combine: \n', cmdText2Workspace + '\n' + cmdCombine #+ '\n' + cmdCombine2

##########################################################
def plotUnfoldCombined( dataFile, sigFiles, bkgFiles, var, sel, reBin, xmin='', xmax='', labX=0.92, labY=0.50, axisX='', axisY='', log=False, ext='png', Norm=False ):
    """"Very specific, takes rootfile from combine and compute unfolding"""

    SigScale = checkDict( next(iter(sigFiles)), dictSamples )['XS'] * args.lumi/ checkDict( next(iter(sigFiles)), dictSamples )['2016']['nevents']
    genMCHisto = sigFiles[next(iter(sigFiles))][0].Get('jetObservables/genJet'+var+sel)
    genMCHisto.Scale( SigScale )
    #genMCHisto.Scale( 1/SigScale, 'width' )

    recoMCHisto = dataFile[next(iter(dataFile))][0].Get('jetObservables/recoJet'+var+'_nom'+sel)
    if args.process.startswith('MC'):
        MCScale = checkDict( next(iter(dataFile)), dictSamples )['XS'] * args.lumi/ checkDict( next(iter(dataFile)), dictSamples )['2016']['nGenWeights']
        recoMCHisto.Scale( MCScale )
        #recoMCHisto.Scale( 1/MCScale, 'width' )
    else:
        for isam in bkgFiles:
            tmpMCHisto = bkgFiles[isam][0].Get('jetObservables/recoJet'+var+'_nom'+sel)
            tmpMCScale = checkDict( isam, dictSamples )['XS'] * args.lumi/ checkDict( isam, dictSamples )['2016']['nGenWeights']
            tmpMCHisto.Scale( tmpMCScale )
            recoMCHisto.Add( tmpMCHisto, -1 )

    if len(reBin)==1:
        genMCHisto.Rebin( reBin[0] )
        recoMCHisto.Rebin( reBin[0] )
    else:
        genMCHisto.Rebin( len(reBin), genMCHisto.GetName()+'_ReBin', array('d', reBin) )
        recoMCHisto.Rebin( len(reBin), recoMCHisto.GetName()+'_ReBin', array('d', reBin) )

    genMCHisto.SetLineWidth(2)
    genMCHisto.SetLineColor(kBlue)
    recoMCHisto.SetLineWidth(2)
    recoMCHisto.SetLineStyle(2)
    recoMCHisto.SetLineColor(kRed)

    combineFile = TFile('higgsCombine'+ivar+'_from'+('Data' if args.process.startswith('data') else 'MC')+'_'+next(iter(sigFiles))+'.MultiDimFit.mH120.root')
    combineTree = combineFile.Get('limit')

    Xvalues = []
    Yvalues = []
    YvaluesCombine = []
    YMaxError = []
    YMinError = []
    for ibin in range(1, genMCHisto.GetNbinsX()+1):
        histoCont = recoMCHisto.GetBinContent(ibin)
        histoErr = recoMCHisto.GetBinError(ibin)
        Xvalues.append( recoMCHisto.GetBinCenter(ibin)  )

        tmpHisto = TH1F('tmp'+str(ibin), 'tmp'+str(ibin), 100, -5, 5)
        combineTree.Draw("r_bin"+str(ibin)+">>tmp"+str(ibin))
        combineCont = tmpHisto.GetMean()
        combineErrUp = combineTree.GetMaximum("r_bin"+str(ibin)) - combineCont
        combineErrDown = combineCont - combineTree.GetMinimum("r_bin"+str(ibin))

        print 'r_bin'+str(ibin), combineCont
        Yvalues.append( histoCont*combineCont )
        YvaluesCombine.append( combineCont )
        histError = 0 if histoCont==0 else TMath.Power( histoErr/histoCont, 2 )
        combineErrorUp = 0 if combineCont==0 else TMath.Power( combineErrUp/combineCont, 2 )
        combineErrorDown = 0 if combineCont==0 else TMath.Power( combineErrDown/combineCont, 2 )
        YMaxError.append( abs( histoCont*combineCont ) * TMath.Sqrt( histError + combineErrorUp  ) )
        YMinError.append( abs( histoCont*combineCont ) * TMath.Sqrt( histError + combineErrorDown  ) )

    UnfoldGraph = TGraphAsymmErrors( len(Xvalues), array( 'd', Xvalues), array( 'd', Yvalues), array( 'd', [0]*len(Xvalues)), array( 'd', [0]*len(Xvalues)), array( 'd', YMinError), array( 'd', YMaxError) )
    UnfoldGraph.SetMarkerStyle(8)
    UnfoldGraph.GetXaxis().SetTitle( genMCHisto.GetXaxis().GetTitle() )
    UnfoldGraph.GetYaxis().SetTitle( 'Events / '+str(genMCHisto.GetBinWidth(1)) )
    UnfoldGraph.GetYaxis().SetTitleOffset( 0.8 )

    legend=TLegend(0.70,0.70,0.90,0.90)
    legend.SetFillStyle(0)
    legend.SetTextSize(0.03)
    legend.AddEntry( UnfoldGraph, 'Unfolding', 'pe' )
    legend.AddEntry( genMCHisto, 'Gen-level MC', 'l' )
    legend.AddEntry( recoMCHisto, ('Data' if args.process.startswith('data') else 'Reco-level MC (Closure)'), 'l' )

    tdrStyle.SetPadRightMargin(0.05)
    tdrStyle.SetPadLeftMargin(0.15)
    can = TCanvas('can', 'can',  10, 10, 750, 750 )
    pad1 = TPad("pad1", "Main",0,0.207,1.00,1.00,-1)
    pad2 = TPad("pad2", "Ratio",0,0.00,1.00,0.30,-1);
    pad1.Draw()
    pad2.Draw()

    pad1.cd()
    tmpPad1= pad1.DrawFrame( 0, 0, 1, 1.5*genMCHisto.GetMaximum() )
    pad1.Modified()
    UnfoldGraph.Draw("P0")
    recoMCHisto.Draw("histe same")
    genMCHisto.Draw("histe same")
    legend.Draw()
    if args.process.startswith('data'):
        CMS_lumi.extraText = "Preliminary"
        CMS_lumi.lumi_13TeV = str( round( (args.lumi/1000.), 2 ) )+" fb^{-1}, 13 TeV, 2016"
    else:
        CMS_lumi.extraText = "Simulation Preliminary"
        CMS_lumi.lumi_13TeV = "13 TeV, 2016"
    CMS_lumi.relPosX = 0.13
    CMS_lumi.CMS_lumi(pad1, 4, 0)

    pad2.cd()
    gStyle.SetOptFit(1)
    pad2.SetGrid()
    pad2.SetTopMargin(0)
    pad2.SetBottomMargin(0.3)
    tmpPad2= pad2.DrawFrame( 0, 0.5, 1, 1.5 )
    tmpPad2.GetXaxis().SetTitle( genMCHisto.GetXaxis().GetTitle() )
    tmpPad2.GetYaxis().SetTitle( "True/Unfolded" )
    tmpPad2.GetYaxis().SetTitleOffset( 0.5 )
    tmpPad2.GetYaxis().CenterTitle()
    tmpPad2.SetLabelSize(0.12, 'x')
    tmpPad2.SetTitleSize(0.12, 'x')
    tmpPad2.SetLabelSize(0.12, 'y')
    tmpPad2.SetTitleSize(0.12, 'y')
    tmpPad2.SetNdivisions(505, 'x')
    tmpPad2.SetNdivisions(505, 'y')
    pad2.Modified()
    hRatioUp = TGraphAsymmErrors( len(Xvalues), array( 'd', Xvalues), array( 'd', YvaluesCombine), array( 'd', [0]*len(Xvalues)), array( 'd', [0]*len(Xvalues)), array( 'd', YMinError), array( 'd', YMaxError) )
    #hRatioUp.SetLineColor(kRed-4)
    #hRatioUp.SetLineWidth(2)
    hRatioUp.SetMarkerStyle(8)
    hRatioUp.Draw('P0')
    #hRatioDown.Draw('P same')

    can.SaveAs('Plots/'+ivar+sel+'_from'+('Data' if args.process.startswith('data') else 'MC')+(''.join(sysUncert))+'_MLU_'+args.version+'.png')



##########################################################################
def loadHistograms( samples, variables, sel, sysUnc=[], isMC=True ):
    """docstring for loadHistograms"""

    SYSUNC = [ '_nom' ] + [ s+u for u in ['Up', 'Down'] for s in sysUnc ]

    allHistos = {}
    for var in variables:
        for isam in samples:
            tmpList = [ 'recoJet'+var+syst+sel for syst in SYSUNC ]
            if isMC: tmpList = tmpList + [ 'genJet'+var+sel ] + [ 'respJet'+var+syst+sel for syst in SYSUNC ]
            for ih in tmpList:
                allHistos[isam+'_'+ih] = samples[isam][0].Get( 'jetObservables/'+ih )
                if isMC:
                    tmpIsam = 'TT' if isam.startswith('data') else isam
                    MCScale = checkDict( tmpIsam, dictSamples )['XS'] * args.lumi / checkDict( tmpIsam, dictSamples )['2016'][( 'nevents' if ih.startswith('gen') else 'nGenWeights')]
                    allHistos[isam+'_'+ih].Scale( MCScale )

                if not ih.startswith('resp'):
                    if len(variables[var])==1:
                        if ih.startswith('reco'):
                            allHistos[isam+'_'+ih+'_genBin'] = allHistos[isam+'_'+ih].Clone()
                            allHistos[isam+'_'+ih+'_genBin'].Rebin( variables[var][0] )
                            allHistos[isam+'_'+ih].Rebin( int(variables[var][0]) )
                        else: allHistos[isam+'_'+ih].Rebin( variables[var][0] )
                    else:
                        if ih.startswith('reco'):
                            newRecoBins = sorted([ (variables[var][i]+variables[var][i+1])/2 for i in range(len(variables[var])-1) ] + variables[var])
                            allHistos[isam+'_'+ih+'_genBin'] = allHistos[isam+'_'+ih].Clone()
                            allHistos[isam+'_'+ih+'_genBin'] = allHistos[isam+'_'+ih+'_genBin'].Rebin( len(variables[var])-1, allHistos[isam+'_'+ih].GetName()+"_Rebin_genBin", array( 'd', variables[var] ) )
                            allHistos[isam+'_'+ih] = allHistos[isam+'_'+ih].Rebin( len(newRecoBins)-1, allHistos[isam+'_'+ih].GetName()+"_Rebin", array( 'd', newRecoBins ) )
                        else:
                            allHistos[isam+'_'+ih] = allHistos[isam+'_'+ih].Rebin( len(variables[var])-1, allHistos[isam+'_'+ih].GetName()+"_Rebin", array( 'd', variables[var] ) )
                else:
                    if len(variables[var])==1: allHistos[isam+'_'+ih].Rebin2D( variables[var][0], int(variables[var][0]) )
                    else:
                        newRecoBins = sorted([ (variables[var][i]+variables[var][i+1]) for i in range(len(variables[var])-1) ] + variables[var])
                        #### fancy way to create variable binning TH2D
                        tmpHisto = TH2F( allHistos[isam+'_'+ih].GetName()+isam+"_Rebin", allHistos[isam+'_'+ih].GetName()+isam+"_Rebin", len(variables[var])-1, array( 'd', variables[var]), len(newRecoBins)-1, array( 'd', newRecoBins) )

                        tmpArrayContent = np.zeros((len(variables[var]), len(newRecoBins)))
                        tmpArrayError = np.zeros((len(variables[var]), len(newRecoBins)))

                        for biny in range( 1, allHistos[isam+'_'+ih].GetNbinsY()+1 ):
                            by = allHistos[isam+'_'+ih].GetYaxis().GetBinCenter( biny )
                            for binx in range( 1, allHistos[isam+'_'+ih].GetNbinsX()+1 ):
                                bx = allHistos[isam+'_'+ih].GetXaxis().GetBinCenter(binx)
                                for iX in range( len(variables[var])-1 ):
                                    for iY in range( len(newRecoBins)-1 ):
                                        if (bx<variables[var][iX+1] and bx>variables[var][iX]) and (by<newRecoBins[iY+1] and by>newRecoBins[iY]):
                                            jbin = allHistos[isam+'_'+ih].GetBin(binx,biny)
                                            tmpArrayContent[iX][iY] = tmpArrayContent[iX][iY] + allHistos[isam+'_'+ih].GetBinContent( jbin )
                                            tmpArrayContent[iX][iY] = tmpArrayContent[iX][iY] + TMath.Power( allHistos[isam+'_'+ih].GetBinError( jbin ), 2 )

                        for biny in range( 1, tmpHisto.GetNbinsY()+1 ):
                            for binx in range( 1, tmpHisto.GetNbinsX()+1 ):
                                tmpHisto.SetBinContent( tmpHisto.GetBin(binx,biny), tmpArrayContent[binx-1][biny-1] )

                        allHistos[isam+'_'+ih] = tmpHisto

                    ##### For tests, projections directly from 2D
                    allHistos[isam+'_genJetfrom_'+ih] = allHistos[isam+'_'+ih].ProjectionY()
                    allHistos[isam+'_recoJetfrom_'+ih] = allHistos[isam+'_'+ih].ProjectionX()

                allHistos[isam+'_'+ih+'_Normalized'] = allHistos[isam+'_'+ih].Clone()
                try: allHistos[isam+'_'+ih+'_Normalized'].Scale( 1/allHistos[isam+'_'+ih+'_Normalized'].Integral() )
                except ZeroDivisionError: continue

    return allHistos



###########################################################################
if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("-p", "--process", action='store', dest="process", default="data", help="Process to unfold: data or MC." )
    parser.add_argument("-s", "--selection", action='store', dest="selection", default="_topSel", help="Selection to unfold: _dijetSel, _WSel, _topSel" )
    ##parser.add_argument("-r", "--runCombine", action='store_true', dest="runCombine", help="Run combine (true)" )
    parser.add_argument('-l', '--lumi', action='store', type=float, default=35920., help='Luminosity, example: 1.' )
    parser.add_argument("-v", "--version", action='store', dest="version", default="v00", help="Version" )

    try: args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)

    inputFolder='Rootfiles/'+args.version
    dataFile = {}
    if args.process.startswith('MC'): dataFile['data'] = [ TFile( inputFolder+'/jetObservables_histograms_TT_TuneCUETP8M2T4_13TeV-powheg-pythia8.root' ), 'Data', 'kBlack' ]
    else: dataFile['data'] = [ TFile( inputFolder+'/jetObservables_histograms_SingleMuonRun2016ALL.root' ), 'Data', 'kBlack' ]

    sigFiles = {}
    #sigFiles['TTJets'] = [ TFile( inputFolder+'/jetObservables_histograms_TTJets_TuneCUETP8M1_13TeV-madgraphMLM-pythia8.root'), 'ttbar (madgraph)', 'kBlue' ]
    sigFiles['TT'] = [ TFile( inputFolder+'/jetObservables_histograms_TT_TuneCUETP8M2T4_13TeV-powheg-pythia8.root'), 'ttbar (madgraph)', 'kBlue' ]

    bkgFiles = {}
    bkgFiles['ST_s-channel_4f_InclusiveDecays'] = [ TFile( inputFolder+'/jetObservables_histograms_ST_s-channel_4f_InclusiveDecays_13TeV-amcatnlo-pythia8.root' ), 'Single top', 'kMagenta' ]
    bkgFiles['ST_t-channel_antitop'] = [ TFile( inputFolder+'/jetObservables_histograms_ST_t-channel_antitop_4f_inclusiveDecays_13TeV-powhegV2-madspin-pythia8_TuneCUETP8M1.root' ), 'Single top', 'kMagenta' ]
    bkgFiles['ST_t-channel_top'] = [ TFile( inputFolder+'/jetObservables_histograms_ST_t-channel_top_4f_inclusiveDecays_13TeV-powhegV2-madspin-pythia8_TuneCUETP8M1.root' ), 'Single top', 'kMagenta' ]
    bkgFiles['ST_tW_antitop'] = [ TFile( inputFolder+'/jetObservables_histograms_ST_tW_antitop_5f_inclusiveDecays_13TeV-powheg-pythia8_TuneCUETP8M2T4.root' ), 'Single top', 'kMagenta' ]
    bkgFiles['ST_tW_top'] = [ TFile( inputFolder+'/jetObservables_histograms_ST_tW_top_5f_inclusiveDecays_13TeV-powheg-pythia8_TuneCUETP8M2T4.root' ), 'Single top', 'kMagenta' ]
    #bkgFiles['WJets'] = [ TFile( inputFolder+'/jetObservables_histograms_WJetsToLNu_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8.root' ), 'WJets', 'kCyan' ]
    ##bkgFiles[] = [ '', TFile( inputFolder+'/jetObservables_histograms_'+ibkg+'.root' ), '', 'kMagenta' ]

    variables = {}
    variables[ 'Tau21' ] = [ 10 ]  ### (reco,gen)
    #variables[ 'Tau21' ] = [ 0, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 1. ]

    sysUncert = [ '_jesTotal', '_jer', '_pu' ]
    #sysUncert = [  ]

    if args.process.endswith('plot'):
        for ivar in variables:
            plotUnfoldCombined( dataFile, sigFiles, bkgFiles, ivar, args.selection, variables[ivar] )
    else: createDatacards( dataFile, sigFiles, bkgFiles, variables, args.selection, sysUncert )

