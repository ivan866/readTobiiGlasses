#!/usr/bin/env python
import argparse
import logging

from datetime import datetime
import webbrowser


from tkinter import *





from data.Corpora import Corpora

import statistics.Descriptive





class ReadTobiiGlasses():

    """Main class of the utility.
    
    Maintains top level window with menus and a status bar.
    
    """


    def __init__(self, gui:bool=True):
        """Setup application and populate menu.
        
        :param gui: Whether to start gui.
        """
        #TODO switch to ?fltk GUI
        #TODO add scrollbar to report textfield
        #FIXME gui freezing while pivoting data
        #TODO command line procedure for gyro2eaf with custom arguments
        #TODO add environment setup script (setup.py), как сделать python package с манифестом пакета
        #TODO !tests and raises error coding style
		#TODO add bash script for batch
        #TODO reroute stderr to report field
        #TODO add cli equivalent commands copied to report with actual arguments
        #TODO sync package API


        self.LOG_FORMAT="%(levelname)s %(asctime)s %(pathname)s, line %(lineno)s: %(message)s"
        logging.basicConfig(filename='Log.log',
                            level=logging.DEBUG,
                            format=self.LOG_FORMAT)
        self.logger=logging.getLogger()





        self.PROJECT_NAME='Read Tobii Glasses'
        self.PROJECT_NAME_SHORT='RTG'
        self.VERSION="0.2"
        self.VIDEO_FRAMERATE=100
        self.PYPER_MANU_ARGS=[128,100,2000,1000,'manu_output']



        self.root = Tk()
        self.root.geometry('640x400')
        self.root.title(self.PROJECT_NAME)
        self.root_menu = Menu(self.root)
        self.root.config(menu = self.root_menu)

        self.report_ta = Text(self.root, bg='lightgray', relief=SUNKEN, wrap=CHAR)
        self.report_ta.insert('1.0', datetime.now().strftime('%Y-%m-%d') + '\n')
        self._report_line_num=1
        self.append_report('ReadTobiiGlasses v{0}.x started.'.format(self.VERSION))
        self.append_report('Interactive GUI session.')
        self.report_ta.pack(side=LEFT, anchor=NW, fill=BOTH)

        self.status_lb = Label(self.root, bd=1, relief=RIDGE, anchor=W)
        self.status_lb.config(text='Please select settings.')
        self.status_lb.pack(side=BOTTOM, fill=X)




        #setup other classes
        self.corpora = Corpora()






        #populate menu
        #FIXME all commands refactor to Command pattern
        settings_menu = Menu(self.root_menu, tearoff=0)
        settings_menu.add_command(label="Select...", command = self.corpora.select_settings)
        settings_menu.add_command(label="Edit...", command = self.corpora.edit_settings)
        self.root_menu.add_cascade(label="Settings", menu = settings_menu)


        data_menu = Menu(self.root_menu, tearoff=0)
        data_menu.add_command(label="Load data", command = self.corpora.load_data)
        # data_menu.add_command(label="Summary and validation", command=self.annotation_data.validate, state=tk.DISABLED)
        # export_menu = Menu(data_menu, tearoff=0)
        # export_menu.add_command(label="Eye events to CSV", command=lambda: self.output_writer.exportFixations(self.annotation_data, 'csv'))
        # export_menu.add_command(label="Eye events to Excel", command=lambda: self.output_writer.exportFixations(self.annotation_data, 'xls'))
        # export_menu.add_command(label="Gyroscope to CSV", command=lambda: self.output_writer.exportGyro(self.annotation_data))
        # export_menu.add_command(label="SQL database", command=lambda: self.output_writer.exportSQL(self.annotation_data))
        # data_menu.add_cascade(label="Export", menu=export_menu)
        self.root_menu.add_cascade(label="Data", menu = data_menu)


        # annotation_menu = Menu(self.root_menu, tearoff=0)
        # annotation_menu.add_command(label="Sanity check", command=lambda: self.set_status('Not implemented.'), state=tk.DISABLED)
        # annotation_menu.add_command(label="Detect ceph motions (gyro)", command=lambda: Annotations.imuToEaf(self, self.annotation_data, settingsReader=self.settings_manager, dataExporter=self.output_writer))
        # annotation_menu.add_command(label="Detect manu motions (pyper)", command=lambda: Annotations.callPyper(self, self.annotation_data, settingsReader=self.settings_manager, dataExporter=self.output_writer, args=self.PYPER_MANU_ARGS))
        # annotation_menu.add_command(label="Convert pyper CSV to EAF", command=lambda: Annotations.pyperToEaf(self, self.annotation_data, settingsReader=self.settings_manager, dataExporter=self.output_writer))
        # annotation_menu.add_command(label="Motion detection quality assessment", command=lambda: Annotations.qualityAssessment(self, self.annotation_data, settingsReader=self.settings_manager, dataExporter=self.output_writer))
        # annotation_menu.add_command(label="Voc/ocul transcript", command=lambda: self.set_status('Not implemented.'))
        # self.root_menu.add_cascade(label="Annotation", menu=annotation_menu)

        # search_menu = Menu(self.root_menu, tearoff=0)
        # gaze_menu = Menu(search_menu, tearoff=0)
        # gaze_menu.add_command(label="All saccades", command=lambda: self.set_status('Not implemented.'))
        # gaze_menu.add_command(label="Tracking lost", command=lambda: self.set_status('Not implemented.'))
        # search_menu.add_cascade(label="Gaze", menu=gaze_menu)
        # voc_menu = Menu(search_menu, tearoff=0)
        # voc_menu.add_command(label="Descending tone", command=lambda: self.set_status('Not implemented.'))
        # voc_menu.add_command(label="Descending-ascending tone", command=lambda: self.set_status('Not implemented.'))
        # search_menu.add_cascade(label="Vocal", menu=voc_menu)
        # manu_menu = Menu(search_menu, tearoff=0)
        # manu_menu.add_command(label="Retraction, no preparation", command=lambda: self.set_status('Not implemented.'))
        # manu_menu.add_command(label="P-S-R", command=lambda: self.set_status('Not implemented.'))
        # search_menu.add_cascade(label="Manual", menu=manu_menu)
        # ceph_menu = Menu(search_menu, tearoff=0)
        # ceph_menu.add_command(label="Upwards movement", command=lambda: self.set_status('Not implemented.'))
        # search_menu.add_cascade(label="Cephalic", menu=ceph_menu)
        # ocul_menu = Menu(search_menu, tearoff=0)
        # ocul_menu.add_command(label="Face/hands", command=lambda: self.set_status('Not implemented.'))
        # ocul_menu.add_command(label="N, following R, following C", command=lambda: self.set_status('Not implemented.'))
        # search_menu.add_cascade(label="Ocular", menu=ocul_menu)
        # bool_menu = Menu(search_menu, tearoff=0)
        # bool_menu.add_command(label="Union...", command=lambda: self.set_status('Not implemented.'))
        # bool_menu.add_command(label="Intersection...", command=lambda: self.set_status('Not implemented.'))
        # bool_menu.add_command(label="Difference...", command=lambda: self.set_status('Not implemented.'))
        # search_menu.add_cascade(label="Boolean", menu=bool_menu)
        # search_menu.add_command(label="Execute SQL query", command=lambda: self.set_status('Not implemented.'))
        # self.root_menu.add_cascade(label="Search", menu=search_menu)

        statistics_menu = Menu(self.root_menu, tearoff=0)
        statistics_menu.add_command(label="Descriptive", command = lambda: statistics.Descriptive(self.corpora)
        # stats_menu.add_command(label="Difference", command=lambda: self.stats.difference(self.pivot_data))
        #stats_menu.add_command(label="ANOVA", command=lambda: self.stats.ANOVA_stats(self.annotation_data, self.pivot_data, dataExporter=self.output_writer))
        self.root_menu.add_cascade(label="Statistic", menu = statistics_menu)

        # viz_menu = Menu(self.root_menu, tearoff=0)
        # plot_menu = Menu(viz_menu, tearoff=0)
        # plot_menu.add_command(label="t-X", command=lambda: self.tempo_plot.drawByIntervals(self.annotation_data))
        # plot_menu.add_command(label="X-Y", command=lambda: self.spatial_plot.drawByIntervals(self.annotation_data))
        # plot_menu.add_command(label="Combined", command=lambda: self.combi_plot.drawByIntervals(self.annotation_data))
        # viz_menu.add_cascade(label="Plot", menu=plot_menu)
        # distr_menu = Menu(viz_menu, tearoff=0)
        # distr_menu.add_command(label="Histogram", command=lambda: self.set_status('Not implemented.'))
        # distr_menu.add_command(label="PDF", command=lambda: self.set_status('Not implemented.'))
        # distr_menu.add_command(label="CDF", command=lambda: self.set_status('Not implemented.'))
        # distr_menu.add_command(label="Spectrogram", command=lambda: self.spectrogram.drawByIntervals(self.annotation_data))
        # viz_menu.add_cascade(label="Distribution", menu=distr_menu)
        # video_menu = Menu(viz_menu, tearoff=0)
        # video_menu.add_command(label="AviSynth player", command=lambda: self.aviSynth_player.launchAVS(self.settings_manager))
        # video_menu.add_command(label="Gaze point overlay", command=lambda: self.set_status('Not implemented.'), state=tk.DISABLED)
        # video_menu.add_command(label="Investigate sync tags", command=lambda: self.set_status('Not implemented.'), state=tk.DISABLED)
        # video_menu.add_command(label="Montage single video...", command=lambda: self.set_status('Not implemented.'))
        # viz_menu.add_cascade(label="Video", menu=video_menu)
        # viz_menu.add_command(label="Heatmap", command=lambda: self.set_status('Not implemented.'))
        # viz_menu.add_command(label="Distance matrix", command=lambda: self.set_status('Not implemented.'))
        # viz_menu.add_command(label="3D scene reconstruction", command=lambda: self.set_status('Not implemented.'), state=tk.DISABLED)
        # self.root_menu.add_cascade(label="Media", menu=viz_menu)


        # help_menu = Menu(self.root_menu, tearoff=0)
        # manuals_menu = Menu(help_menu, tearoff=0)
        # manuals_menu.add_command(label="Tobii coordinate systems", command=lambda: self.goto_web('coordSys'))
        # manuals_menu.add_command(label="Tobii gyroscope data format", command=lambda: self.goto_web('glasses2API'))
        # help_menu.add_cascade(label="Manuals", menu=manuals_menu)
        # help_menu.add_command(label="FAQ", command=lambda: self.goto_web('FAQ'))
        # help_menu.add_command(label="Wiki", command=lambda: self.goto_web('wiki'))
        # help_menu.add_command(label="Repository", command=lambda: self.goto_web('repo'))
        # help_menu.add_command(label="Submit a bug...", command=lambda: self.goto_web('bugs'))
        # self.root_menu.add_cascade(label="Help", menu=help_menu)




        self.logger.debug('starting tk main loop...')
        if gui:
            self.root.mainloop()




    def parse_and_read(self)->None:
        """

        :return:
        """
        self.settings_manager['status_callback'] = self.set_status
        self.annotation_parser['status_callback']  = self.set_status
        self.annotation_parser.read(self.settings_manager, self.annotation_data)






    def CLI_process(self, args:object, serial:bool=False, savePath:str= '')->None:
        """Calls all the functions specified in command line arguments.

        :param args: Command line arguments object.
        :param serial: If this is a serial batch for combining reports to pivot table.
        :param savePath: Directory tree to save batch into.
        :param functions: list of functions to perform with specified settings or batch
        :return:
        """
        if 'desc_stats' in args.functions:
            self.stats.descriptive(self.annotation_data, dataExporter=self.output_writer, serial=serial, savePath=savePath)
        if 'detect_ceph' in args.functions:
            if args.ceph_engine == 'gyro':
                Annotations.imuToEaf(self, self.annotation_data, settingsReader=self.settings_manager, dataExporter=self.output_writer)
            elif args.ceph_engine == 'eavise':
                self.set_status('Not implemented.')
        if 'detect_manu' in args.functions:
            if args.manu_engine=='green_people':
                self.set_status('Not implemented.')
            elif args.manu_engine=='pyper':
                Annotations.callPyper(self, self.annotation_data, settingsReader=self.settings_manager, dataExporter=self.output_writer, args=args.manu_args)
            elif args.manu_engine == 'ssd':
                self.set_status('Not implemented.')

        if not serial:
            sys.exit()




    def append_report(self, text: str, color: str = '#000000') -> None:
        """Appends text to report text widget.

        :param text: Text to append.
        :param color: text color, useful for warnings and successful operations.
        :return:
        """
        # TODO whether to include 'now' timecode - method argument
        self._report_line_num = self._report_line_num + 1
        now = datetime.now().strftime('%H:%M:%S')
        startIndex = '{0}.{1}'.format(self._report_line_num, len(now) + 1)
        endIndex = '{0}.end'.format(self._report_line_num)

        if 'error' in text.lower() or 'unknown' in text.lower() or 'fail' in text.lower() or 'there is no' in text.lower() or color == 'error':
            color = '#FF0000'
        elif 'warn' in text.lower() or color == 'warning':
            color = '#CC4400'
        elif 'success' in text.lower() or 'complete' in text.lower() or color == 'success':
            color = '#006600'
        # TODO ? can add font style for different messages
        # TODO add binding to text to open stat reports

        self.report_ta.config(state=NORMAL)
        self.report_ta.insert(END, now + ' ' + text + '\n')
        self.report_ta.tag_add('line_' + str(self._report_line_num), startIndex, endIndex)
        self.report_ta.tag_config('line_' + str(self._report_line_num), foreground=color)
        self.report_ta.see(END)
        self.report_ta.config(state=DISABLED)

    def report_error(self)->None:
        """Prints current Exception info to report field.

        :return: None.
        """
        eInfo = sys.exc_info()
        self.append_report('{0}: {1}.'.format(eInfo[0].__name__, eInfo[1]), color='error')


    def set_status(self, text:str, color:str= '#000000') -> None:
        """Set status bar text from other code.
        
        :param text: New content for status bar.
        :param color: text color (passed to report field).
        :return: 
        """
        #TODO progress vertical bar rotating in text field
        self.logger.info(text)
        self.append_report(text, color=color)
        self.status_lb.config(text=text)
        self.root.update_idletasks()



    def save_report(self, saveDir:str)->None:
        """Write current report to file.
        
        :param saveDir: Path to write into.
        :return: 
        """
        reportFile = open(saveDir + '/history.txt', 'w')
        reportFile.write(self.report_ta.get('0.0', END))
        reportFile.close()


    #TODO add JAI camera SDK website
    def goto_web(self, page:str)->None:
        """Opens wiki page on GitHub.
        
        :param page: Page tag to open browser for.
        :return: 
        """
        if page=='repo':
            webbrowser.open('https://gitlab.com/ivan866/readTobiiGlasses')
        elif page=='FAQ':
            webbrowser.open('https://gitlab.com/ivan866/readTobiiGlasses/wikis/FAQ')
        elif page=='wiki':
            webbrowser.open('https://gitlab.com/ivan866/readTobiiGlasses/wikis')
        elif page=='bugs':
            webbrowser.open('https://gitlab.com/ivan866/readTobiiGlasses/issues/new')
        elif page=='glasses2API':
            webbrowser.open('http://tobiipro.com/product-listing/tobii-pro-glasses-2-sdk/')
        elif page=='coordSys':
            webbrowser.open('http://developer.tobiipro.com/commonconcepts.html')
        else:
            self.set_status('Unknown URL.')







#TODO change args in wiki on github
#TODO CLI with settings arg only should load and parse them
def main():
    #TODO if manu engine specified, args should be present
    parser = argparse.ArgumentParser(description='Launch ReadTobiiGlasses from the command line.')
    settings_file_group = parser.add_mutually_exclusive_group()
    settings_file_group.add_argument('-s', '--settings-file', type=str, help='Path to settings XML file.')

    parser.add_argument('--desc-statistics', action='append_const', dest='functions', const='desc_stats', help='Calculate descriptive statistics and save detailed report.')

    ceph_group = parser.add_argument_group('ceph', 'Parameters which apply to ceph annotations.')
    ceph_group.add_argument('--detect-ceph', action='append_const', dest='functions', const='detect_ceph', help='Export gyroscope to ELAN.')
    ceph_group.add_argument('--ceph-engine', type=str, choices=['gyro', 'eavise', 'winanalyze'], default='gyro', help='Source of data for ceph motion detection.')
    ceph_group.add_argument('--ceph-args', nargs='+', default=[128, 100, 2000, 1000, 'manu_output'], help='Parameters for the algorithm used for ceph motion detection.')

    manu_group = parser.add_argument_group('manu', 'Parameters which apply to manu annotations.')
    manu_group.add_argument('--detect-manu', action='append_const', dest='functions', const='detect_manu', help='Perform manu motion detection.')
    manu_group.add_argument('--manu-engine', type=str, choices=['green_people', 'pyper', 'tracktor', 'winanalyze', 'ssd'], default='pyper', help='Script or tool to use for manu motion tracking.')
    #TODO default args copy
    manu_group.add_argument('--manu-args', nargs='+', default=[128, 100, 2000, 1000, 'annot'], help='Parameters for the manu CLI tool, e.g. threshold, etc.')
    args = parser.parse_args()

    #with or without command line parameters
    #FIXME если в командной строке указан только файл настроек, какая это сессия считается?
    if args.settings_file:
        rtg = ReadTobiiGlasses(gui=False)
        rtg.append_report('Using CLI with args: {0}.'.format(print(args)))
        if args.settings_file:
            serial = False
            rtg.corpora.select_settings(args.settings_file)
            #TODO
            rtg.annotation_parser.read(rtg.settings_manager, rtg.annotation_data, serial=serial)
            rtg.CLI_process(args=args, serial=serial)
    else:
        rtg = ReadTobiiGlasses()
        rtg.corpora.status_cb=rtg.set_status
        rtg.corpora.error_cb=rtg.report_error



if __name__ == "__main__":
    main()