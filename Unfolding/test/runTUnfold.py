#####################################
#####################################

#!/usr/bin/env python
import argparse, os, shutil, sys
from ROOT import *
import ROOT
from datasets import *
from array import array
import numpy as np
from DrawHistogram import plotSimpleComparison, plotSysComparison
sys.path.insert(0,'../python/')
import CMS_lumi as CMS_lumi
import tdrstyle as tdrstyle
####gReset()
gROOT.SetBatch()
gROOT.ForceStyle()
tdrstyle.setTDRStyle()
gStyle.SetOptStat(0)


def runTUnfold( dataFile, sigFiles, bkgFiles, variables, sel, sysUncert ):
    """docstring for createDataCards"""

    ### Getting input histos
    dataHistos = loadHistograms( dataFile, variables, sel, isMC=False )
    signalHistos = loadHistograms( sigFiles, variables, sel, sysUnc=sysUncert )
    bkgHistos = loadHistograms( bkgFiles, variables, sel, sysUnc=sysUncert ) if args.process.startswith('data') else {}

    for ivar in variables:

        print '|------> Unfolding '+ivar

        ######## Cross check: plotting data vs all MC Scaled
        print '|------> Cross check: plotting data vs all MC'
        allBkgHisto = dataHistos['data_recoJet'+ivar+'_nom'+sel].Clone()
        allBkgHisto.Reset()
        allBkgHistoNorm = allBkgHisto.Clone()
        allBkgHistoGenBin = dataHistos['data_recoJet'+ivar+'_nom'+sel+'_genBin'].Clone()
        allBkgHistoGenBin.Reset()
        for ibkg in bkgHistos:
            if ibkg.endswith('_recoJet'+ivar+'_nom'+sel): allBkgHisto.Add( bkgHistos[ibkg].Clone() )
            if ibkg.endswith('_recoJet'+ivar+'_nom'+sel+'_genBin'): allBkgHistoGenBin.Add( bkgHistos[ibkg].Clone() )
            if ibkg.endswith('_recoJet'+ivar+'_nom'+sel+'_Normalized'): allBkgHistoNorm.Add( bkgHistos[ibkg].Clone() )
        allMCHisto = allBkgHisto.Clone()
        allMCHisto.Add( signalHistos[ next(iter(sigFiles))+'_recoJet'+ivar+'_nom'+sel ].Clone() )
        plotSimpleComparison( dataHistos['data_recoJet'+ivar+'_nom'+sel].Clone(), 'data', allMCHisto, 'allBkgs', ivar+'_from'+('Data' if args.process.startswith('data') else 'MC')+'_'+next(iter(sigFiles))+"_nom", rebinX=variables[ivar][0], version=sel+'_'+args.version  )
        allMCHistoNorm = allBkgHistoNorm.Clone()
        allMCHistoNorm.Add( signalHistos[ next(iter(sigFiles))+'_recoJet'+ivar+'_nom'+sel+"_Normalized" ].Clone() )
        plotSimpleComparison( dataHistos['data_recoJet'+ivar+'_nom'+sel+"_Normalized"].Clone(), 'data', allMCHistoNorm, 'allBkgs', ivar+'_from'+('Data' if args.process.startswith('data') else 'MC')+'_'+next(iter(sigFiles))+"_nom_Normalized", rebinX=variables[ivar][0], version=sel+'_'+args.version  )

        ######## Cross check: plotting response matrix
        tdrStyle.SetPadRightMargin(0.12)
        print '|------> Cross check: plotting response matrix for signal'
        can2D = TCanvas(ivar+'can2D', ivar+'can2D', 750, 500 )
        signalHistos[next(iter(sigFiles))+'_respJet'+ivar+'_nom'+sel].Draw("colz")
        can2D.SaveAs('Plots/'+ivar+'_from'+('Data' if args.process.startswith('data') else 'MC')+'_'+next(iter(sigFiles))+sel+'_responseMatrix'+args.version+'.png')
        can2DNorm = TCanvas(ivar+'can2DNorm', ivar+'can2DNorm', 750, 500 )
        signalHistos[next(iter(sigFiles))+'_respJet'+ivar+'_nom'+sel+'_Normalized'].Draw("colz")
        can2DNorm.SaveAs('Plots/'+ivar+'_from'+('Data' if args.process.startswith('data') else 'MC')+'_'+next(iter(sigFiles))+sel+'Normalized_responseMatrix'+args.version+'.png')

        ####### Removing bkgs from data
        dataMinusBkgs = dataHistos[ 'data_recoJet'+ivar+'_nom'+sel ].Clone()
        dataMinusBkgs.Add( allBkgHisto.Clone(), -1 )
        dataMinusBkgs.Scale( 1/dataMinusBkgs.Integral() )
        dataMinusBkgsGenBin = dataHistos[ 'data_recoJet'+ivar+'_nom'+sel+'_genBin' ].Clone()
        dataMinusBkgsGenBin.Add( allBkgHistoGenBin.Clone(), -1 )
        dataMinusBkgsGenBin.Scale( 1/dataMinusBkgsGenBin.Integral() )

        ######## TUnfold part
        print '|------> TUnfolding starts:'

        ##### Defining options for TUnfold
        tunfolder = ROOT.TUnfoldDensity(
                                            signalHistos[next(iter(sigFiles))+'_respJet'+ivar+'_nom'+sel+'_Normalized'], ### response matrix
                                            #signalHistos[next(iter(sigFiles))+'_respJet'+ivar+'_nom'+sel], ### response matrix
                                            ROOT.TUnfold.kHistMapOutputHoriz,  #### kHistMapOutputVert if x->reco and y->gen, kHistMapOutputHoriz if x->gen and y->reco
                                            ROOT.TUnfold.kRegModeCurvature,   ##### Regularization Mode : ROOT.TUnfold.kRegModeCurvature regularizes based on the 2nd derivative of the output. More information wrt the other options can be gained from reading the source code
                                            ROOT.TUnfold.kEConstraintNone,    ##### Constraint : TUnfold.kEConstraintNone meaning we do not constrain further, the other option is to force constraint of area. (Need to look into this!!)
                                            ROOT.TUnfoldDensity.kDensityModeBinWidth  ##### Density Mode: ROOT.TUnfoldDensity.kDensityModeBinWidth uses the bin width to normalize the event rate in a given bin, accounting for non-uniformity in bin widths as discussed in section 7.2.1 of the TUnfold paper
                                            )

        ##### Defining input (data recoJet )
        print '|------> TUnfolding adding input:'
        #tunfolder.SetInput( dataHistos[ 'data_recoJet'+ivar+'_nom'+sel ].Clone() )
        tunfolder.SetInput( dataMinusBkgs )

        ###### Removing bkgs from data using TUnfold. Better to subtract bkgs beforehand
        #for ibkg in bkgHistos:
        #    if ibkg.endswith('_recoJet'+ivar+'_nom'+sel+'_Normalized'):
        #        print '|--------> Removing this bkg: ', ibkg
        #        tunfolder.SubtractBackground( bkgHistos[ibkg], ibkg )

        ###### Adding SYS unc
        if len(sysUncert)>0 :
            print '|------> TUnfolding adding uncert:'
            for sys in sysUncert:
                plotSysComparison( signalHistos[next(iter(sigFiles))+'_recoJet'+ivar+'_nom'+sel+"_Normalized"],
                                    signalHistos[next(iter(sigFiles))+'_recoJet'+ivar+sys+'Up'+sel+"_Normalized"],
                                    signalHistos[next(iter(sigFiles))+'_recoJet'+ivar+sys+'Down'+sel+"_Normalized"],
                                    ivar+'_'+next(iter(sigFiles)),
                                    sys.split('_')[1],
                                    version=sel+'_'+args.version
                                    )
                for upDown in [ 'Up', 'Down' ]:
                    print sys+upDown
                    tunfolder.AddSysError(
                                        signalHistos[next(iter(sigFiles))+'_respJet'+ivar+sys+upDown+sel+"_Normalized"],
                                        sys+upDown,
                                        ROOT.TUnfold.kHistMapOutputHoriz,
                                        ROOT.TUnfoldSys.kSysErrModeMatrix, #### kSysErrModeMatrix the histogram sysError corresponds to an alternative response matrix. kSysErrModeShift the content of the histogram sysError are the absolute shifts of the response matrix. kSysErrModeRelative the content of the histogram sysError specifies the relative uncertainties
                                        )
                    can2DNorm = TCanvas(ivar+'can2DNorm'+sys+upDown, ivar+'can2DNorm'+sys+upDown, 750, 500 )
                    signalHistos[next(iter(sigFiles))+'_respJet'+ivar+sys+upDown+sel+"_Normalized"].Draw("colz")
                    can2DNorm.SaveAs('Plots/'+ivar+'_from'+('Data' if args.process.startswith('data') else 'MC')+'_'+next(iter(sigFiles))+sel+sys+upDown+'Normalized_responseMatrix'+args.version+'.png')

        ###### Running the unfolding
        print '|------> TUnfolding doUnfold:'
        tunfolder.DoUnfold(0)

        ###### Regularization
#        nScan=50
#        tauMin=0.0
#        tauMax=0.0
#        iBest=0
#
#        logTauX = ROOT.MakeNullPointer(ROOT.TSpline)
#        logTauY = ROOT.MakeNullPointer(ROOT.TSpline)
#        lCurve = ROOT.MakeNullPointer(ROOT.TGraph)
#        ## this method scans the parameter tau and finds the kink in the L curve finally, the unfolding is done for the best choice of tau
#        tunfolder.ScanLcurve(nScan,tauMin,tauMax,lCurve,logTauX,logTauY)
        #########################

        ##### Get output of unfolding
        unfoldHisto = tunfolder.GetOutput("unfoldHisto")

        #### Get various covariances
        print '|------> TUnfolding covariances'
        cov = tunfolder.GetEmatrixTotal("cov", "Covariance Matrix")
        cov_uncorr = tunfolder.GetEmatrixSysUncorr("cov_uncorr", "Covariance Matrix from Uncorrelated Uncertainties")
        cov_uncorr_data = tunfolder.GetEmatrixInput("cov_uncorr_data", "Covariance Matrix from Stat Uncertainties of Input Data")
        unfoldHistowoUnc = unfoldHisto.Clone()        # Unfolding and stat unc
        unfoldHistoStatUnc = unfoldHisto.Clone("unfoldHistoStatUnc")        # Unfolding and stat unc
        unfoldHistoTotUnc = unfoldHisto.Clone("unfoldHistoTotUnc")          # Total uncertainty
        for ibin in range( 0, unfoldHisto.GetNbinsX()+1 ):
            unc_tot = ROOT.TMath.Sqrt( cov.GetBinContent(ibin,ibin) )
            unfoldHistoTotUnc.SetBinContent(ibin, unc_tot )
            unfoldHisto.SetBinError(ibin, unc_tot )


        ##### Get systematic shifts of output
        uncerUnfoldHisto = {}
        if len(sysUncert)>0 :
            print '|------> TUnfolding uncertainties:'
            unfoldHistoSysUnc = unfoldHisto.Clone("unfoldHistoSysUnc")          # Syst uncertainty
            unfoldHistoSysUnc.Reset()
            unfoldHistoSysUnc.SetLineStyle(2)

            for sys in sysUncert:
                for upDown in [ 'Up', 'Down' ]:
                    print sys+upDown
                    uncerUnfoldHisto[ivar+sys+upDown] = tunfolder.GetDeltaSysSource(sys+upDown, "unfoldHisto_"+sys+upDown+"shift", "-1#sigma")
                    try: uncerUnfoldHisto[ivar+sys+upDown].SetLineStyle(2)
                    except ReferenceError: uncerUnfoldHisto.pop( ivar+sys+upDown, None )

                # Create total uncertainty and sys uncertainty plots.
                uncerUnfoldHisto[ivar+sys+'Total'] = unfoldHisto.Clone("unfoldHistoSysUnc")          # Syst uncertainty
                uncerUnfoldHisto[ivar+sys+'Total'].Reset()
                uncerUnfoldHisto[ivar+sys+'Total'].SetLineStyle(3)
                for i in xrange( 0, unfoldHisto.GetNbinsX() + 1):
                    try: yup = abs( uncerUnfoldHisto[ivar+sys+'Up'].GetBinContent(i))
                    except KeyError: yup = 0
                    try: ydn = abs( uncerUnfoldHisto[ivar+sys+'Down'].GetBinContent(i))
                    except KeyError: ydn = 0
                    dy = ROOT.TMath.Sqrt( (yup**2 + ydn**2) )
                    uncerUnfoldHisto[ivar+sys+'Total'].SetBinContent(i, dy )
                unfoldHistoSysUnc.Add( uncerUnfoldHisto[ivar+sys+'Total'] )

        ###### Plot unfolding results
        tdrStyle.SetPadRightMargin(0.05)
        tdrStyle.SetPadLeftMargin(0.15)
        can = TCanvas('can', 'can',  10, 10, 750, 750 )
        pad1 = TPad("pad1", "Main",0,0.207,1.00,1.00,-1)
        pad2 = TPad("pad2", "Ratio",0,0.00,1.00,0.30,-1);
        pad1.Draw()
        pad2.Draw()

        pad1.cd()

        legend=TLegend(0.65,0.65,0.90,0.88)
        legend.SetFillStyle(0)
        legend.SetTextSize(0.03)

        #genJetHisto = signalHistos[ next(iter(sigFiles))+'_genJet'+ivar+sel ].Clone()
        genJetHisto = signalHistos[ next(iter(sigFiles))+'_genJet'+ivar+sel+'_Normalized' ].Clone()
        genJetHisto.Scale(1, 'width')  ### divide by bin width
        genJetHisto.SetLineWidth(2)
        genJetHisto.SetLineColor(1)
        legend.AddEntry( genJetHisto, 'True', 'l' )

        #unfoldHisto = tunfolder.GetOutput("unfolded")
        #if len(variables[ivar])>1: unfoldHisto = unfoldHisto.Rebin( len(variables[ivar])-1, unfoldHisto.GetName()+"_rebin", array( 'd', variables[ivar] ) )
        #else: unfoldHisto.Rebin( variables[ivar][0] )
        unfoldHisto.Scale(1, 'width')  ### divide by bin width
        unfoldHisto.SetMarkerStyle(4)
        unfoldHisto.SetMarkerSize(2)
        unfoldHisto.SetMarkerColor(kRed)
        unfoldHisto.SetLineColor(kRed)
        legend.AddEntry( unfoldHisto, 'Unfolded, total unc', 'pl' )

        unfoldHistowoUnc.Scale(1, 'width')  ### divide by bin width
        unfoldHistowoUnc.SetMarkerStyle(0)
        unfoldHistowoUnc.SetMarkerColor(kRed)
        unfoldHistowoUnc.SetLineColor(kRed-3)
        unfoldHistowoUnc.SetLineWidth(2)
        legend.AddEntry( unfoldHistowoUnc, 'Unfolded, stat+unf unc', 'l' )

        foldHisto = tunfolder.GetFoldedOutput("folded") #, 'folded', 'folded', , False)
        #if len(variables[ivar])>1: foldHisto = foldHisto.Rebin( len(variables[ivar])-1, foldHisto.GetName()+"_rebin", array( 'd', variables[ivar] ) )
        foldHisto.Rebin( 2 )
        foldHisto.Scale(1, 'width')  ### divide by bin width
        foldHisto.SetLineWidth(2)
        foldHisto.SetLineStyle(2)
        foldHisto.SetLineColor(8)
        legend.AddEntry( foldHisto, 'Folded', 'l' )

        if args.process.startswith('data'):
            #recoJetHisto = signalHistos[ next(iter(sigFiles))+'_recoJet'+ivar+'_nom'+sel+'_Normalized' ].Clone()
            recoJetHisto = signalHistos[ next(iter(sigFiles))+'_recoJet'+ivar+'_nom'+sel+'_genBin' ].Clone()
            recoJetHisto.Scale(1/recoJetHisto.Integral(), 'width')  ### divide by bin width
            recoJetHisto.SetLineWidth(2)
            recoJetHisto.SetLineStyle(2)
            recoJetHisto.SetLineColor(kBlue)
            legend.AddEntry( recoJetHisto, 'Reco level MC', 'l' )

        dataJetHisto = dataMinusBkgsGenBin.Clone()
        dataJetHisto.Scale(1/dataJetHisto.Integral(), 'width')  ### divide by bin width
        dataJetHisto.SetLineWidth(2)
        dataJetHisto.SetLineStyle(2)
        dataJetHisto.SetLineColor(kMagenta)
        legend.AddEntry( dataJetHisto, ('Data' if args.process.startswith('data') else 'MC Closure' ), 'l' )

        genJetHisto.GetYaxis().SetTitle( '#frac{1}{d#sigma} #frac{d#sigma}{d(#tauX)}' )
        genJetHisto.GetYaxis().SetTitleOffset(0.8)
        genJetHisto.SetMaximum( 1.2*max([ genJetHisto.GetMaximum(), unfoldHisto.GetMaximum(), unfoldHistowoUnc.GetMaximum(), foldHisto.GetMaximum(), dataJetHisto.GetMaximum() ] )  )

        genJetHisto.Draw( "histe")
        unfoldHisto.Draw( "same")
        unfoldHistowoUnc.Draw( "e1 same")
        foldHisto.Draw( "hist same")
        dataJetHisto.Draw( "hist same")
        if args.process.startswith('data'): recoJetHisto.Draw( "hist same")

        legend.Draw()
        if args.process.startswith('data'):
            CMS_lumi.extraText = "Preliminary"
            CMS_lumi.lumi_13TeV = str( round( (lumi/1000.), 2 ) )+" fb^{-1}, 13 TeV, 2016"
        else:
            CMS_lumi.extraText = "Simulation Preliminary"
            CMS_lumi.lumi_13TeV = "13 TeV, 2016"
        CMS_lumi.relPosX = 0.11
        CMS_lumi.CMS_lumi(pad1, 4, 0)

        pad2.cd()
        gStyle.SetOptFit(1)
        pad2.SetGrid()
        pad2.SetTopMargin(0)
        pad2.SetBottomMargin(0.3)
        tmpPad2= pad2.DrawFrame( 0, 0.5, 1, 1.5 )
        tmpPad2.GetXaxis().SetTitle( genJetHisto.GetXaxis().GetTitle() )
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
        hRatioUp = TGraphAsymmErrors()
        hRatioUp.Divide( genJetHisto, unfoldHisto, 'pois' )
        #hRatioUp.SetLineColor(kRed-4)
        #hRatioUp.SetLineWidth(2)
        hRatioUp.SetMarkerStyle(8)
        hRatioUp.Draw('P0')
        #hRatioDown.Draw('P same')

        can.SaveAs('Plots/'+ivar+sel+'_from'+('Data' if args.process.startswith('data') else 'MC')+(''.join(sysUncert))+'_Tunfold_'+args.version+'.png')

        canUnc = TCanvas('canUnc', 'canUnc',  10, 10, 750, 500 )
        #canUnc.SetLogy()

        legend=TLegend(0.70,0.65,0.90,0.88)
        legend.SetFillStyle(0)
        legend.SetTextSize(0.03)
        legend.AddEntry( unfoldHistoTotUnc, 'Total Unc', 'l' )

        #unfoldHistoTotUnc.SetMinimum(0.00001)
        unfoldHistoTotUnc.SetLineWidth(2)
        unfoldHistoTotUnc.Scale( 1/unfoldHistoTotUnc.Integral() )
        unfoldHistoTotUnc.GetYaxis().SetTitle('Fractional Uncertainty')
        unfoldHistoTotUnc.Draw('hist')

        if len(sysUncert)>0 :
            legend.AddEntry( unfoldHistoSysUnc, 'Total Syst Unc', 'l' )
            unfoldHistoSysUnc.Scale( 1/unfoldHistoTotUnc.Integral() )
            unfoldHistoSysUnc.SetLineWidth(2)
            unfoldHistoSysUnc.Draw("hist same")
            dummy=2
            for k in uncerUnfoldHisto:
                if k.endswith('Total'):
                    print k
                    legend.AddEntry( uncerUnfoldHisto[k], k.split('_')[1].split('Total')[0], 'l' )
                    uncerUnfoldHisto[k].SetLineColor(dummy)
                    uncerUnfoldHisto[k].SetLineWidth(2)
                    uncerUnfoldHisto[k].Scale( 1/unfoldHistoTotUnc.Integral() )
                    uncerUnfoldHisto[k].Draw("hist same")
                    dummy=dummy+1

        legend.Draw()
        CMS_lumi.extraText = "Simulation Preliminary"
        #CMS_lumi.lumi_13TeV = str( round( (lumi/1000.), 2 ) )+" fb^{-1}, 13 TeV, 2016"
        CMS_lumi.lumi_13TeV = "13 TeV, 2016"
        CMS_lumi.relPosX = 0.11
        CMS_lumi.CMS_lumi(canUnc, 4, 0)

        canUnc.SaveAs('Plots/'+ivar+sel+'_from'+('Data' if args.process.startswith('data') else 'MC')+(''.join(sysUncert))+'_Tunfold_UNC_'+args.version+'.png')

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
                    MCScale = checkDict( tmpIsam, dictSamples )['XS'] * args.lumi / checkDict( tmpIsam, dictSamples )['2016']['nGenWeights']
                    allHistos[isam+'_'+ih].Scale( MCScale )

                if not ih.startswith('resp'):
                    if len(variables[var])==1:
                        if ih.startswith('reco'):
                            allHistos[isam+'_'+ih+'_genBin'] = allHistos[isam+'_'+ih].Clone()
                            allHistos[isam+'_'+ih+'_genBin'].Rebin( variables[var][0] )
                            allHistos[isam+'_'+ih].Rebin( int(variables[var][0]/2.) )
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
                    if len(variables[var])==1: allHistos[isam+'_'+ih].Rebin2D( variables[var][0], int(variables[var][0]/2.) )
                    else:
                        newRecoBins = sorted([ (variables[var][i]+variables[var][i+1])/2 for i in range(len(variables[var])-1) ] + variables[var])
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
    sigFiles['TTJets'] = [ TFile( inputFolder+'/jetObservables_histograms_TTJets_TuneCUETP8M1_13TeV-madgraphMLM-pythia8.root'), 'ttbar (madgraph)', 'kBlue' ]
    #sigFiles['TT'] = [ TFile( inputFolder+'/jetObservables_histograms_TT_TuneCUETP8M2T4_13TeV-powheg-pythia8.root'), 'ttbar (madgraph)', 'kBlue' ]

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

    runTUnfold( dataFile, sigFiles, bkgFiles, variables, args.selection, sysUncert )

