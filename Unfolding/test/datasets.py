#!/usr/bin/env python
### For xsec calculation: grep miniAOD datasets.py | awk '{ print $4 }' | sed "s/'//g" | sed  's/"//g' | sed 's/\,//g' > calculateXSectionAndFilterEfficiency/datasets.txt

dictSamples = {

    'TT' : {
        '2016' :  {
            'miniAOD' : [ '/TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/RunIISummer16MiniAODv3-PUMoriond17_94X_mcRun2_asymptotic_v3-v1/MINIAODSIM' ],
            'nanoAOD' : [ '/TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/algomez-TTTuneCUETP8M2T413TeV-powheg-pythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER' ],
            'skimmer' : [ '/TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/algomez-jetObservables_Skimmer_v02-dafc15ff64439ee3efd0c8e48ce3e57e/USER' ],
            'nevents' : 76915549.,
            'nGenWeights' : 76489216.00,
            },
        '2017' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        '2018' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        'XS' : 7.306e+02, # +- 5.572e-01 pb
    },
    'TTJets' : {
        '2016' :  {
            'miniAOD' : [ '/TTJets_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/RunIISummer16MiniAODv3-PUMoriond17_94X_mcRun2_asymptotic_v3-v1/MINIAODSIM' ],
            'nanoAOD' : [ '/TTJets_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/algomez-TTJetsTuneCUETP8M113TeV-madgraphMLM-pythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER' ],
            'skimmer' : [ '/TTJets_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/algomez-jetObservables_Skimmer_TTJets_TuneCUETP8M1_13TeV-madgraphMLM-pythia8_v02-dafc15ff64439ee3efd0c8e48ce3e57e/USER' ],
            'nevents' : 10199051.,
            'nGenWeights' : 7662481.00,
            },
        '2017' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        '2018' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        'XS' : 5.093e+02, # +- 4.456e-01 pb
    },
    'QCD_Pt-15to7000_TuneCUETP8M1_FlatP6_13TeV_pythia8' : {
        '2016' :  {
            'miniAOD' : [ '/QCD_Pt-15to7000_TuneCUETP8M1_FlatP6_13TeV_pythia8/RunIISummer16MiniAODv3-PUMoriond17_94X_mcRun2_asymptotic_v3-v2/MINIAODSIM' ],
            'nanoAOD' : [ '/QCD_Pt-15to7000_TuneCUETP8M1_FlatP6_13TeV_pythia8/kadatta-QCDPt-15to7000TuneCUETP8M1FlatP613TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794X-3de7f16b11abe7d2f2c8fb8b12121ea5/USER' ],
            'skimmer' : [ '' ],
            'nevents' : 9951232.,
            'nGenWeights' : 00,
            },
        '2017' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        '2018' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        'XS' : 1.973e+09, # +- 7.754e+05 pb
    },
    'ST_s-channel_4f_InclusiveDecays' : {
        '2016' :  {
            'miniAOD' : [ '/ST_s-channel_4f_InclusiveDecays_13TeV-amcatnlo-pythia8/RunIISummer16MiniAODv3-PUMoriond17_94X_mcRun2_asymptotic_v3-v1/MINIAODSIM' ],
            'nanoAOD' : [ '/ST_s-channel_4f_InclusiveDecays_13TeV-amcatnlo-pythia8/algomez-STs-channel4fInclusiveDecays13TeV-amcatnlo-pythia8RunIISummer16MiniAODv3-PUMoriond17-dafc15ff64439ee3efd0c8e48ce3e57e/USER ' ],
            'skimmer' : [ '/ST_s-channel_4f_InclusiveDecays_13TeV-amcatnlo-pythia8/algomez-jetObservables_Skimmer_v02-dafc15ff64439ee3efd0c8e48ce3e57e/USER' ],
            'nevents' : 2989199.,
            'nGenWeights' : 30289975.20,
            },
        '2017' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        '2018' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        'XS' : 1.012e+01, # +- 1.334e-02 pb
    },
    'ST_t-channel_antitop' : {
        '2016' :  {
            'miniAOD' : [ '/ST_t-channel_antitop_4f_inclusiveDecays_13TeV-powhegV2-madspin-pythia8_TuneCUETP8M1/RunIISummer16MiniAODv3-PUMoriond17_94X_mcRun2_asymptotic_v3-v1/MINIAODSIM' ],
            'nanoAOD' : [ '/ST_t-channel_antitop_4f_inclusiveDecays_13TeV-powhegV2-madspin-pythia8_TuneCUETP8M1/algomez-STt-channelantitop4finclusiveDecays13TeV-powhegV2-madspin-pythia8TuneCUETP8M1-dafc15ff64439ee3efd0c8e48ce3e57e/USER' ],
            'skimmer' : [ '/ST_t-channel_antitop_4f_inclusiveDecays_13TeV-powhegV2-madspin-pythia8_TuneCUETP8M1/algomez-jetObservables_Skimmer_v02-dafc15ff64439ee3efd0c8e48ce3e57e/USER' ],
            'nevents' : 38811017.,
            'nGenWeights' : 37877067.00,
            },
        '2017' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        '2018' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        'XS' : 7.441e+01, # +- 4.171e-01 pb
    },
    'ST_t-channel_top' : {
        '2016' :  {
            'miniAOD' : [ '/ST_t-channel_top_4f_inclusiveDecays_13TeV-powhegV2-madspin-pythia8_TuneCUETP8M1/RunIISummer16MiniAODv3-PUMoriond17_94X_mcRun2_asymptotic_v3-v1/MINIAODSIM' ],
            'nanoAOD' : [ "/ST_t-channel_top_4f_inclusiveDecays_13TeV-powhegV2-madspin-pythia8_TuneCUETP8M1/algomez-STt-channeltop4finclusiveDecays13TeV-powhegV2-madspin-pythia8TuneCUETP8M1-dafc15ff64439ee3efd0c8e48ce3e57e/USER" ],
            'skimmer' : [ '/ST_t-channel_top_4f_inclusiveDecays_13TeV-powhegV2-madspin-pythia8_TuneCUETP8M1/algomez-jetObservables_Skimmer_v02-dafc15ff64439ee3efd0c8e48ce3e57e/USER' ],
            'nevents' : 67105876.,
            'nGenWeights' : 66826980.00,
            },
        '2017' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        '2018' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        'XS' : 1.233e+02, # +- 7.721e-01 pb
    },
    'ST_tW_antitop' : {
        '2016' :  {
            'miniAOD' : [ "/ST_tW_antitop_5f_inclusiveDecays_13TeV-powheg-pythia8_TuneCUETP8M2T4/RunIISummer16MiniAODv3-PUMoriond17_94X_mcRun2_asymptotic_v3-v1/MINIAODSIM" ],
            'nanoAOD' : [ "/ST_tW_antitop_5f_inclusiveDecays_13TeV-powheg-pythia8_TuneCUETP8M2T4/algomez-STtWantitop5finclusiveDecays13TeV-powheg-pythia8TuneCUETP8M2T4-dafc15ff64439ee3efd0c8e48ce3e57e/USER" ],
            'skimmer' : [ '/ST_tW_antitop_5f_inclusiveDecays_13TeV-powheg-pythia8_TuneCUETP8M2T4/algomez-jetObservables_Skimmer_v02-dafc15ff64439ee3efd0c8e48ce3e57e/USER' ],
            'nevents' : 998276.,
            'nGenWeights' : 998276.00,
            },
        '2017' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        '2018' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        'XS' : 3.806e+01, # +- 3.055e-02 pb
    },
    'ST_tW_top' : {
        '2016' :  {
            'miniAOD' : [ '/ST_tW_top_5f_inclusiveDecays_13TeV-powheg-pythia8_TuneCUETP8M2T4/RunIISummer16MiniAODv3-PUMoriond17_94X_mcRun2_asymptotic_v3-v1/MINIAODSIM' ],
            'nanoAOD' : [ "/ST_tW_top_5f_inclusiveDecays_13TeV-powheg-pythia8_TuneCUETP8M2T4/algomez-STtWtop5finclusiveDecays13TeV-powheg-pythia8TuneCUETP8M2T4-dafc15ff64439ee3efd0c8e48ce3e57e/USER" ],
            'skimmer' : [ '/ST_tW_top_5f_inclusiveDecays_13TeV-powheg-pythia8_TuneCUETP8M2T4/algomez-jetObservables_Skimmer_v02-dafc15ff64439ee3efd0c8e48ce3e57e/USER' ],
            'nevents' : 992024.,
            'nGenWeights' : 992024.00,
            },
        '2017' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        '2018' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        'XS' : 3.809e+01, # +- 3.050e-02 pb
    },
    'WJetsToLNu' : {
        '2016' :  {
            'miniAOD' : [ '/WJetsToLNu_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8/RunIISummer16MiniAODv3-PUMoriond17_94X_mcRun2_asymptotic_v3-v1/MINIAODSIM', '/WJetsToLNu_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8/RunIISummer16MiniAODv3-PUMoriond17_94X_mcRun2_asymptotic_v3_ext2-v1/MINIAODSIM' ],
            'nanoAOD' : [ '/WJetsToLNu_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8/algomez-WJetsToLNuTuneCUETP8M113TeV-amcatnloFXFX-pythia8RunIISummer16MiniAODv3-PUMoriond1794X-dafc15ff64439ee3efd0c8e48ce3e57e/USER', '/WJetsToLNu_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8/algomez-WJetsToLNuTuneCUETP8M113TeV-amcatnloFXFX-pythia8RunIISummer16MiniAODv3-PUMoriond1794X_ext2-v1-dafc15ff64439ee3efd0c8e48ce3e57e/USER' ],
            'skimmer' : [ '/WJetsToLNu_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8/algomez-jetObservables_Skimmer_v02-dafc15ff64439ee3efd0c8e48ce3e57e/USER' ],
            'nevents' : 24120319.,
            'nGenWeights' : 611509190272.00,
            },
        '2017' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        '2018' :  {
            'nanoAOD' : [ '' ],
            'skimmer' : [ '' ],
            'nevents' : 00,
            'nGenWeights' : 00,
            },
        'XS' : 6.038e+04, # +- 1.238e+02 pb
    },
#    '' : {
#        '2016' :  {
#            'nanoAOD' : [ '' ],
#            'skimmer' : [ '' ],
#            'nevents' : 00,
#            'nGenWeights' : 00,
#            },
#        '2017' :  {
#            'nanoAOD' : [ '' ],
#            'skimmer' : [ '' ],
#            'nevents' : 00,
#            'nGenWeights' : 00,
#            },
#        '2018' :  {
#            'nanoAOD' : [ '' ],
#            'skimmer' : [ '' ],
#            'nevents' : 00,
#            'nGenWeights' : 00,
#            },
#        'XS' : 0,
#    },
}

def checkDict( string, dictio ):
    return next(v for k,v in dictio.items() if string.startswith(k))

