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
echo "python {pythonFile} --sample {datasets} --selection {selection}"
python {pythonFile} --sample {datasets} --selection {selection}
fi
    '''
    open('runPostProc'+options.datasets+'.sh', 'w').write(BASH_SCRIPT.format(**options.__dict__))


def submitJobs( job, inputFiles, unitJobs ):

    from CRABAPI.RawCommand import crabCommand
    from WMCore.Configuration import Configuration
    config = Configuration()

    from httplib import HTTPException

    # We want to put all the CRAB project directories from the tasks we submit here into one common directory.                                                        =
    # That's why we need to set this parameter (here or above in the configuration file, it does not matter, we will not overwrite it).
    config.section_("General")
    config.General.workArea = options.dir
    #config.General.transferLogs = False
    #config.General.transferOutputs = True

    config.section_("JobType")
    config.JobType.pluginName = 'Analysis'
    config.JobType.psetName = 'PSet.py'
    #config.JobType.maxMemoryMB = 5000
    config.JobType.allowUndistributedCMSSW = True

    config.section_("Data")
    #config.Data.publication = True
    #config.Data.publishDBS = 'phys03'
    config.Data.inputDBS = 'phys03'
    config.Data.ignoreLocality = True

    config.section_("Site")
    config.Site.storageSite = options.storageSite
    config.Site.whitelist = ['T1_US_FNAL','T2_CH_CSCS','T3_US_FNALLPC']
    #config.Site.blacklist = ['T2_US_Florida','T3_TW_*','T2_BR_*','T2_GR_Ioannina','T2_BR_SPRACE','T2_RU_IHEP','T2_PL_Swierk','T2_KR_KNU','T3_TW_NTU_HEP']


    def submit(config):
        try:
            crabCommand('submit', config = config)
        except HTTPException, hte:
            print 'Cannot execute command'
            print hte.headers


    requestname = 'jetObservables_Skimmer_'+ job + '_' +options.version
    print requestname
    config.JobType.scriptExe = 'runPostProc'+options.datasets+'.sh'
    config.JobType.inputFiles = [ options.pythonFile ,'haddnano.py', 'keep_and_drop.txt']
    config.JobType.sendPythonFolder  = True

    if job.startswith(('Single', 'JetHT')): config.Data.lumiMask = '/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions16/13TeV/Final/Cert_271036-284044_13TeV_PromptReco_Collisions16_JSON.txt'
    #config.Data.userInputFiles = inputFiles
    config.Data.inputDataset = inputFiles
    config.Data.splitting = 'EventAwareLumiBased' if job.startswith('QCD') else 'FileBased'
    config.Data.unitsPerJob = unitJobs
    #config.Data.outputPrimaryDataset = job

    # since the input will have no metadata information, output can not be put in DBS
    config.JobType.outputFiles = [ 'jetObservables_nanoskim.root', 'jetObservables_histograms.root']
    config.Data.outLFNDirBase = '/store/user/'+os.environ['USER']+'/jetObservables/'

    if len(requestname) > 100: requestname = (requestname[:95-len(requestname)])
    print 'requestname = ', requestname
    config.General.requestName = requestname
    config.Data.outputDatasetTag = requestname
    print 'Submitting ' + config.General.requestName + ', dataset = ' + job
    print 'Configuration :'
    print config
    submit(config)
    #try : submit(config)
    #except : print 'Not submitted.'



if __name__ == '__main__':

    usage = ('usage: python multicrab_nSubProducer.py --datasets NAMEOFDATASET -d DIR -v VERSION')

    parser = OptionParser(usage=usage)
    parser.add_option(
            "-D", "--dir",
            dest="dir", default="crab_projects",
            help=("The crab directory you want to use "),
            )
    parser.add_option(
            "-d", "--datasets",
            dest="datasets", default='all',
            help=("File listing datasets to run over"),
            )
    parser.add_option(
            "-S", "--storageSite",
            dest="storageSite", default="T3_CH_PSI",
            help=("Storage Site"),
            )
    parser.add_option(
            "-v", "--version",
            dest="version", default="102X_v00",
            help=("Version of output"),
            )
    parser.add_option(
            "-s", "--selection",
            dest="selection", default="dijet",
            help=("Selection: dijet, Wtop"),
            )
    parser.add_option(
            "-p", "--pythonFile",
            dest="pythonFile", default="jetObservables_nSubProducer.py",
            help=("python file to run"),
            )


    (options, args) = parser.parse_args()


    dictSamples = {}

    dictSamples['JetHT2016B'] = ['/JetHT/algomez-JetHT_Run2016B-17Jul2018_ver2-v2-c59ef3ac16263506c0c61b1b9e3fa54b/USER', 1 ]
    dictSamples['JetHT2016C'] = ['/JetHT/algomez-JetHT_Run2016C-17Jul2018-v1-c59ef3ac16263506c0c61b1b9e3fa54b/USER', 1 ]
    dictSamples['JetHT2016D'] = ['/JetHT/algomez-JetHT_Run2016D-17Jul2018-v1-c59ef3ac16263506c0c61b1b9e3fa54b/USER', 1 ]
    dictSamples['JetHT2016E'] = ['/JetHT/algomez-JetHT_Run2016E-17Jul2018-v1-c59ef3ac16263506c0c61b1b9e3fa54b/USER', 1 ]
    dictSamples['JetHT2016F'] = ['/JetHT/algomez-JetHT_Run2016F-17Jul2018-v1-c59ef3ac16263506c0c61b1b9e3fa54b/USER', 1 ]
    dictSamples['JetHT2016G'] = ['/JetHT/algomez-JetHT_Run2016G-17Jul2018-v1-c59ef3ac16263506c0c61b1b9e3fa54b/USER', 2 ]
    dictSamples['JetHT2016H'] = ['/JetHT/algomez-JetHT_Run2016H-17Jul2018-v1-c59ef3ac16263506c0c61b1b9e3fa54b/USER', 2 ]

    dictSamples['SingleMuon2016B'] = ['/SingleMuon/algomez-SingleMuon_Run2016B-17Jul2018_ver2-v1-c59ef3ac16263506c0c61b1b9e3fa54b/USER', 2 ]
    dictSamples['SingleMuon2016C'] = ['/SingleMuon/algomez-SingleMuon_Run2016C-17Jul2018-v1-c59ef3ac16263506c0c61b1b9e3fa54b/USER', 2 ]
    dictSamples['SingleMuon2016D'] = ['/SingleMuon/algomez-SingleMuon_Run2016D-17Jul2018-v1-c59ef3ac16263506c0c61b1b9e3fa54b/USER', 2 ]
    dictSamples['SingleMuon2016E'] = ['/SingleMuon/algomez-SingleMuon_Run2016E-17Jul2018-v1-c59ef3ac16263506c0c61b1b9e3fa54b/USER', 2 ]
    dictSamples['SingleMuon2016F'] = ['/SingleMuon/algomez-SingleMuon_Run2016F-17Jul2018-v1-c59ef3ac16263506c0c61b1b9e3fa54b/USER', 2 ]
    dictSamples['SingleMuon2016G'] = ['/SingleMuon/algomez-SingleMuon_Run2016G-17Jul2018-v1-c59ef3ac16263506c0c61b1b9e3fa54b/USER', 2 ]
    dictSamples['SingleMuon2016H'] = ['/SingleMuon/kadatta-SingleMuon_Run2016H-17Jul2018-v1-5ffac30f2c7d804e43ff60dc5e74139f/USER', 2 ]

    dictSamples['TT_TuneCUETP8M2T4_13TeV-powheg-pythia8'] = [ '/TT_TuneCUETP8M2T4_13TeV-powheg-pythia8/algomez-TTTuneCUETP8M2T413TeV-powheg-pythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 2 ]
    dictSamples['TTJets_TuneCUETP8M1_13TeV-madgraphMLM-pythia8'] = ['/TTJets_TuneCUETP8M1_13TeV-madgraphMLM-pythia8/algomez-TTJetsTuneCUETP8M113TeV-madgraphMLM-pythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 2 ]
    dictSamples['ST_s-channel'] = ['/ST_s-channel_4f_InclusiveDecays_13TeV-amcatnlo-pythia8/algomez-STs-channel4fInclusiveDecays13TeV-amcatnlo-pythia8RunIISummer16MiniAODv3-PUMoriond17-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 2 ]
    dictSamples['ST_t-channel_antitop'] = ['/ST_t-channel_antitop_4f_inclusiveDecays_13TeV-powhegV2-madspin-pythia8_TuneCUETP8M1/algomez-STt-channelantitop4finclusiveDecays13TeV-powhegV2-madspin-pythia8TuneCUETP8M1-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 2 ]
    dictSamples['ST_t-channel_top'] = ["/ST_t-channel_top_4f_inclusiveDecays_13TeV-powhegV2-madspin-pythia8_TuneCUETP8M1/algomez-STt-channeltop4finclusiveDecays13TeV-powhegV2-madspin-pythia8TuneCUETP8M1-dafc15ff64439ee3efd0c8e48ce3e57e/USER", 2 ]
    dictSamples['ST_tW_antitop'] = ["/ST_tW_antitop_5f_inclusiveDecays_13TeV-powheg-pythia8_TuneCUETP8M2T4/algomez-STtWantitop5finclusiveDecays13TeV-powheg-pythia8TuneCUETP8M2T4-dafc15ff64439ee3efd0c8e48ce3e57e/USER", 2 ]
    dictSamples['ST_tW_top'] = ["/ST_tW_top_5f_inclusiveDecays_13TeV-powheg-pythia8_TuneCUETP8M2T4/algomez-STtWtop5finclusiveDecays13TeV-powheg-pythia8TuneCUETP8M2T4-dafc15ff64439ee3efd0c8e48ce3e57e/USER", 2 ]
    dictSamples['WJetsToLNu'] = ['/WJetsToLNu_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8/algomez-WJetsToLNuTuneCUETP8M113TeV-amcatnloFXFX-pythia8RunIISummer16MiniAODv3-PUMoriond1794X-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 2 ]
    dictSamples['WJetsToLNu_EXT'] = ['/WJetsToLNu_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8/algomez-WJetsToLNuTuneCUETP8M113TeV-amcatnloFXFX-pythia8RunIISummer16MiniAODv3-PUMoriond1794X_ext2-v1-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 2 ]

    #dictSamples[ 'QCD_Pt15to7000' ] = [ '/QCD_Pt-15to7000_TuneCUETP8M1_FlatP6_13TeV_pythia8/kadatta-QCDPt-15to7000TuneCUETP8M1FlatP613TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794X-3de7f16b11abe7d2f2c8fb8b12121ea5/USER', 100000 ]
    dictSamples['QCD_Pt170to300'] = ['/QCD_Pt_170to300_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt170to300TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 100000 ]
    dictSamples['QCD_Pt300to470'] = ['/QCD_Pt_300to470_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt300to470TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 100000 ]
    dictSamples['QCD_Pt470to600'] = ['/QCD_Pt_470to600_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt470to600TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 100000 ]
    dictSamples['QCD_Pt600to800'] = ['/QCD_Pt_600to800_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt600to800TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 10000 ]
    dictSamples['QCD_Pt800to1000'] = ['/QCD_Pt_800to1000_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt800to1000TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 10000 ]
    dictSamples['QCD_Pt1000to1400'] = ['/QCD_Pt_1000to1400_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt1000to1400TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 10000 ]
    dictSamples['QCD_Pt1400to1800'] = ['/QCD_Pt_1400to1800_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt1400to1800TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 1000 ]
    dictSamples['QCD_Pt1800to2400'] = ['/QCD_Pt_1800to2400_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt1800to2400TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 1000 ]
    dictSamples['QCD_Pt2400to3200'] = [ '/QCD_Pt_2400to3200_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt2400to3200TuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 1000 ]
    dictSamples['QCD_Pt3200toInf'] = ['/QCD_Pt_3200toInf_TuneCUETP8M1_13TeV_pythia8/algomez-QCDPt3200toInfTuneCUETP8M113TeVpythia8RunIISummer16MiniAODv3-PUMoriond1794XmcRun2-dafc15ff64439ee3efd0c8e48ce3e57e/USER', 1000 ]

    processingSamples = {}
    if 'all' in options.datasets:
        for sam in dictSamples: processingSamples[ sam ] = dictSamples[ sam ]
    else:
        for sam in dictSamples:
            if sam.startswith( options.datasets ): processingSamples[ sam ] = dictSamples[ sam ]

    if len(processingSamples)==0: print 'No sample found. \n Have a nice day :)'

    for isam in processingSamples:

        if isam.startswith('QCD') or isam.startswith('JetHT'): options.selection = 'dijet'
        else: options.selection = 'Wtop'

        options.datasets = isam
        print('Creating bash file...')
        createBash()

        print ("dataset %s has %d files" % (processingSamples[isam], len(processingSamples[isam][0])))
        submitJobs( isam, processingSamples[isam][0], processingSamples[isam][1] )
