import os, shutil, json
import xmlserializer
from copy import deepcopy
from modeler import ModelerLodded
import csur
from csur import Segment
from csur import StandardWidth as SW
from thumbnail import draw

class AssetMaker:

    connectgroup = {'None': 'None', '11': 'WideTram', '33': 'SingleTram', '31': 'NarrowTram',
                    '3-1': 'DoubleTrain', '00': 'CenterTram', '1-1': 'SingleTrain'}

    names = {'g': 'basic', 'e': 'elevated', 'b': 'bridge', 't': 'tunnel', 's': 'slope'}
    shaders = {'g': 'Road', 'e': 'RoadBridge', 'b': 'RoadBridge', 't': 'RoadBridge', 's': 'RoadBridge'}
    suffix = {'e': 'express', 'w': 'weave', 'c': 'compact', 'p': 'parking'}
    
    segment_presets = {}
    node_presets = {}
    lanes = {}
    props = {}

    def __init__(self, dir, config_file='csur_blender.ini',
                 template_path='templates', output_path='output', bridge=False, tunnel=True):
        self.modeler = ModelerLodded(os.path.join(dir, config_file), bridge, tunnel)
        self.output_path = os.path.join(dir, output_path)
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        self.template_path = os.path.join(dir, template_path)
        self.workdir = dir
        self.bridge = bridge
        self.tunnel = tunnel
        self.assetdata = {}
        with open(os.path.join(self.template_path, 'segment_presets.json'), 'r') as f:
            self.segment_presets = json.load(f)
        with open(os.path.join(self.template_path, 'node_presets.json'), 'r') as f:
            self.node_presets = json.load(f)
        with open(os.path.join(self.template_path, 'lanes.json'), 'r') as f:
            self.lanes = json.load(f)
        with open(os.path.join(self.template_path, 'props.json'), 'r') as f:
            self.props = json.load(f)

    def __initialize_assetinfo(self, asset):
        self.assetdata = {}
        self.assetdata['name'] = str(asset.get_model('g'))
        for v in AssetMaker.names.values():
            with open(os.path.join(self.template_path, 'netinfo', '%s.json' % v), 'r') as f:
                jsondata = json.load(f)
                self.assetdata[v] = jsondata
            with open(os.path.join(self.template_path, 'net_ai', '%s.json' % v), 'r') as f:
                jsondata = json.load(f)
                self.assetdata['%sAI' % v] = jsondata
            self.assetdata['%sModel' % v] = {'segmentMeshes': {'CSMesh': []}, 'nodeMeshes': {'CSMesh': []}}
        return self.assetdata

    def __create_mesh(self, color, shader, name, tex=None):
        color = {'float': [str(x) for x in color]}
        csmesh = {}
        csmesh['color'] = color
        csmesh['shader'] = 'Custom/Net/%s' % shader
        csmesh['name'] = name
        csmesh['texture'] = tex or name.split('_')[-1]
        return csmesh

    def __add_segment(self, name, model, mode='g', texmode=None, preset='default', color=[0.5, 0.5, 0.5]):
        self.modeler.save(model, os.path.join(self.output_path, name + '.FBX'))
        modename = AssetMaker.names[mode[0]]
        texmode = texmode or modename
        newmesh = self.__create_mesh(color, AssetMaker.shaders[mode[0]], name, texmode)
        self.assetdata['%sModel' % modename]['segmentMeshes']['CSMesh'].append(newmesh)
        segmentinfo = deepcopy(self.segment_presets[preset])
        self.assetdata[modename]['m_segments']['Segment'].append(segmentinfo)

    def __add_node(self, name, model, mode='g', texmode=None, preset='default', color=[0.5, 0.5, 0.5], connectgroup=None):
        self.modeler.save(model, os.path.join(self.output_path, name + '.FBX'))
        modename = AssetMaker.names[mode[0]]
        texmode = texmode or modename
        newmesh = self.__create_mesh(color, AssetMaker.shaders[mode[0]], name, texmode)     
        self.assetdata['%sModel' % modename]['nodeMeshes']['CSMesh'].append(newmesh)
        nodeinfo = deepcopy(self.node_presets[preset])
        self.assetdata[modename]['m_nodes']['Node'].append(nodeinfo)
        if connectgroup:
            self.assetdata[modename]['m_nodes']['Node'][-1]['m_connectGroup'] = connectgroup

    def __create_segment(self, asset, mode):
        modename = AssetMaker.names[mode[0]]
        seg = asset.get_model(mode)
        name = str(seg)
        # make model
        seg_lanes, seg_struc = self.modeler.make(seg, mode)
        if len(mode) > 1:
            modename += AssetMaker.suffix[mode[1]]
        if asset.is_twoway() and asset.roadtype=='b' and asset.center()[0] == 0:
            preset_lane = 'default' if asset.left.nl() == asset.right.nl() else 'default_asym'
            preset_struc = 'default'
        else:
            preset_lane = preset_struc = 'default_noncentered'
        # save model and textures
        if asset.is_twoway() and asset.roadtype == 'r':
            self.__add_segment('%s_%slanes_f' % (name, mode), seg_lanes[0], mode=mode[0], preset=preset_lane, texmode='lane')
            self.__add_segment('%s_%slanes_r' % (name, mode), seg_lanes[1], mode=mode[0], preset=preset_lane, texmode='lane')
        else:
            self.__add_segment('%s_%slanes' % (name, mode), seg_lanes, mode=mode[0], preset=preset_lane, texmode='lane')
        self.__add_segment('%s_%s' % (name, modename), seg_struc, mode=mode[0], preset=preset_struc, texmode='tunnel' if mode[0] == 's' else None)

    def __create_stop(self, asset, mode, busstop):
        if not busstop:
            raise ValueError("stop type should be specified!")
        modename = AssetMaker.names[mode[0]]
        seg = asset.get_model(mode)
        name = str(seg) + bool(busstop) * '_stop_%s' % busstop
        if busstop == 'brt':
            seg_lanes, seg_struc, brt_f, brt_both = self.modeler.make(seg, mode, busstop=busstop)
            preset = 'stopignored'
        else:
            seg_lanes, seg_struc = self.modeler.make(seg, mode, busstop=busstop)
            preset = 'stop' + busstop
        if len(mode) > 1:
            modename += AssetMaker.suffix[mode[1]]
        self.__add_segment('%s_%slanes' % (name, mode), seg_lanes, mode=mode[0], preset=preset, texmode='lane')
        self.__add_segment('%s_%s' % (name, modename), seg_struc, mode=mode[0], preset=preset)
        if busstop == 'brt':
            self.__add_segment('%s_brt_single' % name, brt_f, mode=mode[0], preset='stopsingle', texmode='brt_platform')
            self.__add_segment('%s_brt_double' % name, brt_f, mode=mode[0], preset='stopdouble', texmode='brt_platform')


    def __create_node(self, asset):
        seg = asset.get_model('g')
        name = str(seg) + '_node'
        pavement, junction = self.modeler.make_node(seg)
        self.__add_node('%s_pavement' % name, pavement, preset='default', texmode='node')
        self.__add_node('%s_junction' % name, junction, preset='trafficlight', texmode='node')

    def __create_dcnode(self, asset, target_median=None, asym_mode=None):
        MW = 1.875
        seg = asset.get_model('g')
        if target_median is None:
            medians = None
            target_median = self.__get_mediancode(asset)
        else:
            split = 1 if target_median[0] != '-' else 2
            medians = [-int(target_median[:split])*MW, int(target_median[split:])*MW]
        if asym_mode != 'invert':
            if asym_mode == 'restore':
                dcnode, target_median = self.modeler.make_asym_restore_node(seg)
                print(target_median)
                name = '%s_restorenode' % str(seg)
            elif asym_mode == 'expand':
                dcnode, target_median = self.modeler.make_asym_invert_node(seg, halved=True) 
                print(target_median)
                name = '%s_expandnode' % str(seg)
            else:
                dcnode = self.modeler.make_dc_node(seg, target_median=medians)
                name = '%s_dcnode_%s' % (str(seg), target_median)
            self.__add_node(name, dcnode, preset='direct', connectgroup=AssetMaker.connectgroup[target_median], texmode='lane')
        else:
            # note that "bend node" is actually a segment in the game
            asym_forward, asym_backward = self.modeler.make_asym_invert_node(seg, halved=False)
            self.__add_segment('%s_asymforward' % str(seg), asym_forward, mode='g', preset='asymforward', texmode='lane')
            self.__add_segment('%s_asymbackward' % str(seg), asym_backward, mode='g', preset='asymbackward', texmode='lane')
        
    def __create_brtnode(self, asset):
        if not asset.is_twoway():
            raise ValueError("BRT station should be created on two-way roads!")
        mode = 'g'
        seg = asset.get_model(mode)
        blocks = asset.right.get_all_blocks()[0]
        seg_l = csur.CSURFactory(mode=mode, roadtype='b').get(
                                    blocks[0].x_left, blocks[0].nlanes)
        seg_r = csur.CSURFactory(mode=mode, roadtype='s').get([
                                    blocks[1].x_left - SW.MEDIAN, blocks[1].x_left], blocks[1].nlanes)
        dc_seg = csur.CSURFactory.fill_median(seg_l, seg_r, 's')
        dc_seg = csur.TwoWay(dc_seg.reverse(), dc_seg)
        model = self.modeler.convert_to_dcnode(dc_seg, keep_bikelane=False)
        self.__add_node('%s_brtnode' % str(seg), model, 
                        preset='direct', 
                        connectgroup=AssetMaker.connectgroup[self.__get_mediancode(asset)], 
                        texmode='lane')


    def __create_lanes(self, seg, mode, reverse=False):
        if isinstance(seg, csur.TwoWay):
            self.__create_lanes(seg.left, mode, reverse=True)
            self.__create_lanes(seg.right, mode, reverse=False)
        else:
            modename = AssetMaker.names[mode[0]]
            shift_lane_flag = False
            for i, zipped in enumerate(zip(seg.start, seg.end)):
                u_start, u_end = zipped
                lane = None
                if u_start == u_end:
                    di_start = di_end = 0
                    if not shift_lane_flag and seg.roadtype() == 's' and min(seg.n_lanes()) > 1 and u_start == Segment.LANE:
                        if seg.x_start[0] - seg.x_end[0] > SW.LANE / 2:
                            di_end = 1
                            shift_lane_flag = True
                            continue
                        elif seg.x_end[0] - seg.x_start[0] > SW.LANE / 2:
                            di_start = 1
                            shift_lane_flag = True
                            continue
                    pos_start = (seg.x_start[i + di_start] + seg.x_start[i + 1 + di_start]) / 2
                    pos_end = (seg.x_end[i + di_end] + seg.x_end[i + 1 + di_end]) / 2
                    pos = (pos_start + pos_end) / 2
                    if reverse:
                        pos = -pos
                    if u_start == Segment.LANE:
                        lane = deepcopy(self.lanes['car'])
                    elif u_start == Segment.BIKE:
                        lane = deepcopy(self.lanes['bike'])
                    elif u_start == Segment.SIDEWALK:
                        lane = deepcopy(self.lanes['ped'])
                    if lane is not None:
                        lane['m_position'] = str(pos)
                        if u_start != Segment.SIDEWALK:
                            if reverse:
                                lane['m_direction'] = 'Backward'
                                lane['m_finalDirection'] = 'Backward'
                            else:
                                lane['m_direction'] = 'Forward'
                                lane['m_finalDirection'] = 'Forward'
                        self.assetdata[modename]['m_lanes']['Lane'].append(lane)

    def __get_mediancode(self, asset):
        if not asset.is_twoway():
            return 'None'
        medians = asset.n_central_median()
        return str(medians[0]) + str(medians[1])

    def __write_netAI(self, asset, mode):
        seg = asset.get_model(mode)
        modename = AssetMaker.names[mode[0]]
        if mode[0] == 'g' and asset.is_twoway():
            self.assetdata['%sAI' % modename]['m_trafficLights'] = 'true'

    def __write_info(self, asset, mode):
        seg = asset.get_model(mode)
        modename = AssetMaker.names[mode[0]]
        info = self.assetdata[modename]
        if type(seg) == csur.TwoWay:
            info["m_connectGroup"] = AssetMaker.connectgroup[self.__get_mediancode(asset)]
            halfwidth = min([max(seg.right.x_start), max(seg.left.x_start)])
            if seg.right.start[-1] == Segment.SIDEWALK:
                halfwidth -= 1.25
            if asset.asym()[0] > 0:
                halfwidth += asset.asym()[0] * 1e-5
        else:
            info["m_connectGroup"] = "None"
            halfwidth = max([max(seg.x_start), max(seg.x_end)])
            if seg.start[-1] == Segment.SIDEWALK:
                halfwidth -= 1.25
            info["m_createPavement"] = "false"
            info["m_flattenTerrain"] = "false"
            info["m_clipTerrain"] = "false"
            info["m_enableBendingNodes"] = "false"
            info["m_clipSegmentEnds"] = "false"
            info["m_minCornerOffset"] = "0"
        info["m_halfWidth"] = "%.8f" % halfwidth
        if asset.roadtype == 'b':
            info["m_enableBendingSegments"] = "true"

    def writetoxml(self, asset):
        path = os.path.join(self.output_path, str(asset.get_model('g')) + '_data.xml')
        xmlserializer.write(self.assetdata, 'RoadAssetInfo', path)

    def write_thumbnail(self, asset):
        path = os.path.join(self.output_path, str(asset.get_model('g')))
        draw(asset, os.path.join(self.workdir, 'img/color.ini'), path)
        for mode in ['disabled', 'hovered', 'focused', 'pressed']:
            draw(asset, os.path.join(self.workdir, 'img/color.ini'), path, mode=mode)
    
    def make(self, asset, weave=False):
        self.__initialize_assetinfo(asset)
        modes = ['g', 'e']
        if self.tunnel:
            modes.append('t')
        if weave:
            modes = [x + 'w' for x in modes]
        if asset.roadtype == 'b':
            if self.bridge:
                modes.append('b')
            if self.tunnel:
                modes.append('s')
        # build segments
        for mode in modes:
            self.__create_segment(asset, mode)
        # build node
        if asset.is_twoway() and asset.roadtype == 'b':
            n_central_median = asset.n_central_median()
            self.__create_node(asset)
            if n_central_median[0] == n_central_median[1]:
                self.__create_dcnode(asset)
                if n_central_median[0] == 1:
                    self.__create_dcnode(asset, target_median='33')
            else:
                if n_central_median[0] + n_central_median[1] > 0:
                    self.__create_dcnode(asset)
                    self.__create_dcnode(asset, asym_mode='expand')
                self.__create_dcnode(asset, asym_mode='invert')   
                self.__create_dcnode(asset, asym_mode='restore')
            self.__create_stop(asset, 'g', 'single')
            self.__create_stop(asset, 'g', 'double')
        # write data
        for mode in modes:
            seg = asset.get_model(mode)
            self.__create_lanes(seg, mode)
            self.__write_netAI(asset, mode)
            self.__write_info(asset, mode)
        self.writetoxml(asset)
        self.write_thumbnail(asset)
        return self.assetdata

    def make_singlemode(self, asset, mode):
        self.__initialize_assetinfo(asset)
        self.__create_segment(asset, mode)
        if asset.is_twoway() and asset.roadtype == 'b':
            self.__create_node(asset)
        seg = asset.get_model(mode)
        self.__create_lanes(seg, mode)
        self.__write_netAI(asset, mode)
        self.__write_info(asset, mode)
        self.writetoxml(asset)
        self.write_thumbnail(asset)
        return self.assetdata


    def make_brt(self, asset):
        self.__initialize_assetinfo(asset)
        self.__create_stop(asset, 'g', 'brt')
        self.__create_node(asset)
        self.__create_brtnode(asset)
        seg = asset.get_model('g')
        self.__create_lanes(seg, 'g')
        self.__write_netAI(asset, 'g')
        self.__write_info(asset, 'g')
        self.assetdata['basic']["m_connectGroup"] = "None"
        self.writetoxml(asset)
        self.write_thumbnail(asset)
        return self.assetdata