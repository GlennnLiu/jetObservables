#!/usr/bin/env python
"""
This is a small script that submits a config over many datasets
"""
import os
from optparse import OptionParser

def make_list(option, opt, value, parser):
    setattr(parser.values, option.dest, value.split(','))

def createBash():

    BASH_SCRIPT = '''
#this is not meant to be run locally
#
echo Check if TTY
if [ "`tty`" != "not a tty" ]; then
  echo "YOU SHOULD NOT RUN THIS IN INTERACTIVE, IT DELETES YOUR LOCAL FILES"
else

###ls -lR .
echo "ENV..................................."
env
echo "VOMS"
voms-proxy-info -all
echo "CMSSW BASE, python path, pwd"
echo $CMSSW_BASE
echo $PYTHON_PATH
echo $PWD
rm -rf $CMSSW_BASE/lib/
rm -rf $CMSSW_BASE/src/
rm -rf $CMSSW_BASE/module/
rm -rf $CMSSW_BASE/python/
mv lib $CMSSW_BASE/lib
mv src $CMSSW_BASE/src
mv python $CMSSW_BASE/python

echo Found Proxy in: $X509_USER_PROXY
echo "python  jetObservables_crab_extNanoAOD.py ......."
python jetObservables_crab_extNanoAOD.py $1
fi
    '''
    open('runPostProc.sh', 'w').write(BASH_SCRIPT.format(**options.__dict__))


def submitJobs( job, inputFiles, unitJobs ):


    from WMCore.Configuration import Configuration
    config = Configuration()

    from CRABAPI.RawCommand import crabCommand
    from httplib import HTTPException


    # We want to put all the CRAB project directories from the tasks we submit here into one common directory.                                                        =
    # That's why we need to set this parameter (here or above in the configuration file, it does not matter, we will not overwrite it).
    config.section_("General")
    config.General.workArea = options.dir
    config.General.transferLogs = False
    config.General.transferOutputs = True

    config.section_("JobType")
    config.JobType.pluginName = 'Analysis'
    config.JobType.psetName = 'PSet.py'

    config.section_("Data")
    #config.Data.publication = True
    #config.Data.publishDBS = 'phys03'
    config.Data.inputDBS = 'phys03'

    config.section_("Site")
    config.Site.storageSite = options.storageSite
    #config.Site.whitelist = ['T2_US_Wisconsin','T2_CH_CSCS','T2_US_Caltech','T2_US_MIT']
    #config.Site.blacklist = ['T2_US_Florida','T3_TW_*','T2_BR_*','T2_GR_Ioannina','T2_BR_SPRACE','T2_RU_IHEP','T2_PL_Swierk','T2_KR_KNU','T3_TW_NTU_HEP']


    def submit(config):
        try:
            crabCommand('submit', config = config)
        except HTTPException, hte:
            print 'Cannot execute command'
            print hte.headers


    requestname = 'jetObservables_'+ job + '_' +options.version
    print requestname
    config.JobType.scriptExe = 'runPostProc.sh'
    config.JobType.inputFiles = [ 'PSet.py','runPostProc.sh', 'jetObservables_crab_extNanoAOD.py' ,'haddnano.py', 'keep_and_drop.txt']
    config.JobType.sendPythonFolder  = True

    #config.Data.userInputFiles = inputFiles
    config.Data.inputDataset = inputFiles
    config.Data.splitting = 'FileBased'
    config.Data.unitsPerJob = unitJobs
    #config.Data.outputPrimaryDataset = job

    # since the input will have no metadata information, output can not be put in DBS
    config.JobType.outputFiles = [ 'jetObservables_nanoskim.root']
    config.Data.outLFNDirBase = '/store/user/'+os.environ['USER']+'/jetObservables/'

    if len(requestname) > 100: requestname = (requestname[:95-len(requestname)])
    print 'requestname = ', requestname
    config.General.requestName = requestname
    config.Data.outputDatasetTag = requestname
    print 'Submitting ' + config.General.requestName + ', dataset = ' + job
    print 'Configuration :'
    print config
    try :
        from multiprocessing import Process

        p = Process(target=submit, args=(config,))
        p.start()
        p.join()
        #submit(config)
    except :
        print 'Not submitted.'



if __name__ == '__main__':

    usage = ('usage: python submit_all.py -c CONFIG -d DIR -f DATASETS_FILE')

    parser = OptionParser(usage=usage)
    parser.add_option(
            "-D", "--dir",
            dest="dir", default="crab_projects",
            help=("The crab directory you want to use "),
            metavar="DIR" )
    parser.add_option(
            "-d", "--datasets",
            dest="datasets", default='all',
            help=("File listing datasets to run over"),
            metavar="FILE" )
    parser.add_option(
            "-s", "--storageSite",
            dest="storageSite", default="T3_CH_PSI",
            help=("Storage Site"),
            metavar="SITE")
    parser.add_option(
            "-v", "--version",
            dest="version", default="102X_v00",
            help=("Version of output"),
            metavar="VER")


    (options, args) = parser.parse_args()


    dictSamples = {}
    #dictSamples['BulkGravtoWW_M-3000'] = ['/BulkGravToWW_narrow_M-3000_13TeV-madgraph/RunIISummer16MiniAODv2-PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v6_ext1-v1/MINIAODSIM',1]  

    dictSamples['SingleTop_1'] = ['/ST_t-channel_antitop_4f_inclusiveDecays_13TeV-powhegV2-madspin-pythia8_TuneCUETP8M1/algomez-STt-channelantitop4finclusiveDecays13TeV-powhegV2-madspin-pythia8TuneCUETP8M1-dafc15ff64439ee3efd0c8e48ce3e57e/USER',1]

    dictSamples['SingleTop_2'] = ["/ST_t-channel_top_4f_inclusiveDecays_13TeV-powhegV2-madspin-pythia8_TuneCUETP8M1/algomez-STt-channeltop4finclusiveDecays13TeV-powhegV2-madspin-pythia8TuneCUETP8M1-dafc15ff64439ee3efd0c8e48ce3e57e/USER",1]

    dictSamples['Wjets_1'] = ['/WJetsToLNu_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8/algomez-WJetsToLNuTuneCUETP8M113TeV-amcatnloFXFX-pythia8RunIISummer16MiniAODv3-PUMoriond1794X-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 1]

    dictSamples['Wjets_2'] = ['/WJetsToLNu_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8/algomez-WJetsToLNuTuneCUETP8M113TeV-amcatnloFXFX-pythia8RunIISummer16MiniAODv3-PUMoriond1794X_ext2-v1-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 1]

    dictSamples['SingleMuon2016G'] = ['/SingleMuon/chmclean-SingleMuon_Run2016G-17Jul2018-v1-c59ef3ac16263506c0c61b1b9e3fa54b/USER',1]

    dictSamples['SingleMuon2016H'] = ['/SingleMuon/kadatta-SingleMuon_Run2016H-17Jul2018-v1-5ffac30f2c7d804e43ff60dc5e74139f/USER',1]
    
    dictSamples['TTbar_1'] = [ '/TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/algomez-TTTuneCUETP8M2T413TeV-powheg-pythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 1 ]
    dictSamples['TTbar_2'] = ['/TTJets_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/algomez-TTJetsTuneCUETP8M113TeV-madgraphMLM-pythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 1]

#dictSamples['BulkGravtoWW_M-2000'] = ['/BulkGravToWW_narrow_M-2000_13TeV-madgraph/RunIISummer16MiniAODv2-PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v6_ext1-v1/MINIAODSIM',1]
    
    #dictSamples['QCD_170to300'] = ['/QCD_Pt_170to300_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt170to300TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER',1]
    #dictSamples['QCD_300to470'] = ['/QCD_Pt_300to470_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt300to470TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER',1]
    #dictSamples['QCD_470to600'] = ['/QCD_Pt_470to600_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt470to600TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER',1]
    #dictSamples['QCD_600to800'] = ['/QCD_Pt_600to800_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt600to800TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER',1]
    #dictSamples['QCD_800to1000'] = ['/QCD_Pt_800to1000_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt800to1000TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER',1]
    #dictSamples['QCD_1000to1400'] = ['/QCD_Pt_1000to1400_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt1000to1400TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER',1]
    #dictSamples['QCD_1400to1800'] = ['/QCD_Pt_1400to1800_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt1400to1800TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER',1]
    #dictSamples['QCD_1800to2400'] = ['/QCD_Pt_1800to2400_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt1800to2400TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER',1]
    #dictSamples['QCD_2400to3200'] = [ '/QCD_Pt_2400to3200_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt2400to3200TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER',1]
    #dictSamples['QCD_3200toInf'] = ['/QCD_Pt_3200toInf_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt3200toInfTuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER',1]    '''
    #/TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/algomez-TTTuneCUETP8M2T413TeV-powheg-pythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER
    
    '''
    #dictSamples['SingleMuon_Run2017'] = [ ['root://cmseos.fnal.gov//store/user/asparker/NanoAODJMARTools-skims//nanoskim-JetsandLepton-SingleMuon17B-trees.root', 'root://cmseos.fnal.gov//store/user/asparker/NanoAODJMARTools-skims//nanoskim-JetsandLepton-SingleMuon17C-trees.root', 'root://cmseos.fnal.gov//store/user/asparker/NanoAODJMARTools-skims//nanoskim-JetsandLepton-SingleMuon17D-trees.root', 'root://cmseos.fnal.gov//store/user/asparker/NanoAODJMARTools-skims//nanoskim-JetsandLepton-SingleMuon17E-trees.root', 'root://cmseos.fnal.gov//store/user/asparker/NanoAODJMARTools-skims//nanoskim-JetsandLepton-SingleMuon17F-trees.root' ], 1 ]

    #dictSamples['SingleElectron_Run2017'] = [ ['root://cmseos.fnal.gov//store/user/asparker/NanoAODJMARTools-skims/nanoskim-JetsandLepton-Data-SingleElectron17B-trees.root', 'root://cmseos.fnal.gov//store/user/asparker/NanoAODJMARTools-skims/nanoskim-JetsandLepton-Data-SingleElectron17C-trees.root', 'root://cmseos.fnal.gov//store/user/asparker/NanoAODJMARTools-skims/nanoskim-JetsandLepton-Data-SingleElectron17D-trees.root', 'root://cmseos.fnal.gov//store/user/asparker/NanoAODJMARTools-skims/nanoskim-JetsandLepton-Data-SingleElectron17E-trees.root', 'root://cmseos.fnal.gov//store/user/asparker/NanoAODJMARTools-skims/nanoskim-JetsandLepton-Data-SingleElectron17F-trees.root'], 1 ]

    #dictSamples['TTbar_2017'] = [ ['root://cmseos.fnal.gov//store/user/asparker/NanoAODJMARTools-skims/nanoskim-JetsandLepton-94XMC-TTJets_TuneCP5_13TeV-amcatnloFXFX-pythia8-1of3-trees.root', 'root://cmseos.fnal.gov//store/user/asparker/NanoAODJMARTools-skims/nanoskim-JetsandLepton-94XMC-TTJets_TuneCP5_13TeV-amcatnloFXFX-pythia8-2of3-trees.root', 'root://cmseos.fnal.gov//store/user/asparker/NanoAODJMARTools-skims/nanoskim-JetsandLepton-94XMC-TTJets_TuneCP5_13TeV-amcatnloFXFX-pythia8-3of3-trees.root', 'root://cmseos.fnal.gov//store/user/asparker/NanoAODJMARTools-skims/nanoskim-JetsandLepton-94XMC-TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8-trees.root' ], 1 ]
    '''
    processingSamples = {}
    if 'all' in options.datasets:
        for sam in dictSamples: processingSamples[ sam ] = dictSamples[ sam ]
    else:
        for sam in dictSamples:
            if sam.startswith( options.datasets ): processingSamples[ sam ] = dictSamples[ sam ]

    if len(processingSamples)==0: print 'No sample found. \n Have a nice day :)'

    for isam in processingSamples:

        print('Creating bash file...')
        createBash()

        print ("dataset %s has %d files" % (processingSamples[isam], len(processingSamples[isam][0])))
        submitJobs( isam, processingSamples[isam][0], processingSamples[isam][1] )
