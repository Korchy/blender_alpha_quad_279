# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
# Created by Kushiro

import math

from numpy.core.function_base import linspace
from numpy.lib.function_base import average
import bpy
import bmesh

from mathutils import Matrix, Vector, Quaternion


import mathutils
import itertools


import math
from bpy.props import (
    FloatProperty,
    IntProperty,
    BoolProperty,
    EnumProperty,
    FloatVectorProperty,
)

import pprint
import time

from . import gui



# class Vert:
#     def __init__(self) -> None:
#         self.co = None
#         self.plist = []
#         self.move = Vector()
#         self.boundary = False
#         self.face_boundary = False
#         self.links = []


# class Vloop:
#     def __init__(self, co=None) -> None:
#         self.vert = None        
#         self.next = None
#         self.prev = None        
#         if co != None:
#             self.vert = Vert()
#             self.vert.co = co

#         self.ptype = ''
#         self.v2 = None
#         self.vk1 = None
#         self.vk2 = None
#         self.pv1 = None
#         self.pv2 = None
#         self.pvk1 = None
#         self.pvk2 = None



#     def angle(self):
#         m1 = self.next.vert.co - self.vert.co
#         m2 = self.prev.vert.co - self.vert.co
#         if m1.length == 0 or m2.length == 0:
#             return 0
#         return m1.angle(m2)

#     def link_next(self, v2):
#         self.next = v2
#         v2.prev = self

#     def link_prev(self, v2):
#         self.prev = v2
#         v2.next = self

#     def copy(self):
#         vp = Vloop()
#         vp.vert = self.vert
#         return vp

#     def copy_new(self):
#         vp = Vloop(Vector())
#         vp.vert.co = self.vert.co.copy()
#         return vp        

#     def is_concave(self, sn):
#         m2 = self.vert.co - self.prev.vert.co
#         c1 = m2.cross(sn)
#         m1 = self.next.vert.co - self.vert.co

#         if m1.cross(m2).length < 0.001:
#             return False

#         if c1.length == 0 or m1.length == 0:
#             return False
#         if c1.angle(m1) < math.radians(90):
#             return True
#         else:
#             return False
        

class AlphaQuadOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "mesh.alpha_quad_operator"
    bl_label = "Alpha Quad"
    bl_options = {"REGISTER", "UNDO"}
    #, "GRAB_CURSOR", "BLOCKING"


    prop_plen: FloatProperty(
        name="Quad size",
        description="Define the size of quad",
        default=0.4,
        min = 0.4,
        step=1,
    )    



    prop_size_multiplier: FloatProperty(
        name="Size Multipler (auto reset)",
        description="Size Multipler for quad size",
        default=1.0,
        step=0.1,
        min = 0.01,
    )    


    prop_keep_edge: BoolProperty(
        name="Keep sharp edge",
        description="Do not smooth the sharp edge",
        default=False,
    )    

    prop_keep_edge_angle: FloatProperty(
        name="Edge Angle",
        description="Define the Edge Angle for keeping sharp edge",
        default=75,
        min = 0,
        max = 180,
        step=10,
    )    



    def get_bm(self):
        obj = bpy.context.active_object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        return bm


    def process(self, context):
        gui.lines = []
        gui.textpos = []
        self.plen = 0.05
        self.cuts = 1
        self.part = self.prop_plen * self.prop_size_multiplier
        bm = self.get_bm()     

        sel = [f1 for f1 in bm.faces if f1.select]
        original = set(sel)
        excluded = self.get_excluded(bm, original)

        for f1 in sel:
            self.even_cut_simple(bm, f1)

        # self.current_milli_time()
        fss = []
        for f1 in sel:
            f1.select = False
            # finner, fss = self.inseting(bm, f1)             
            # self.even_cut(bm, f1)
            fs = self.div_faces_base(bm, f1)
            fss += fs

        # self.current_milli_time()
        for f2 in fss:
            self.div_faces_quad(bm, f2)

        # self.current_milli_time()
        self.sub_div(bm, excluded)
        # self.current_milli_time()
        self.process_smooth(bm, excluded)
        # self.current_milli_time()

        # bmesh.ops.delete(bm, geom=[f1], context='FACES')       
        obj = bpy.context.active_object                
        me = bpy.context.active_object.data
        bmesh.update_edit_mesh(me)   



    def current_milli_time(self):
        if hasattr(self, 'ptime') == False:
            self.ptime = 0
        p = round(time.time() * 1000)
        print(p - self.ptime)
        self.ptime = p


    def inseting(self, bm, f1):    
        plen = self.plen 
        sn = f1.normal
        coss = [p.vert.co for p in f1.loops]        
        vmap = {}
        inner1 = []
        fss = []
        for co in coss:
            p1 = None
            for p2 in f1.loops:
                if p2.vert.co == co:
                    p1 = p2
                    break
            if p1 == None:
                break            
            m1 = p1.link_loop_next.vert.co - p1.vert.co
            m2 = p1.link_loop_prev.vert.co - p1.vert.co
            m3 = self.mid_line(m1, m2, sn)
            m3 = m3.normalized() * plen
            co3 = p1.vert.co + m3               
            
            if p1.is_convex == False:                
                if p1.calc_angle() < math.radians(120):
                    leng1 = p1.link_loop_next.vert.co - p1.vert.co
                    leng2 = p1.link_loop_prev.vert.co - p1.vert.co
                    off1 = m2.normalized() * min(plen, leng1.length * 0.4)
                    off2 = m1.normalized() * min(plen, leng2.length * 0.4)
                    k1 = p1.vert.co - off1
                    k2 = p1.vert.co - off2
                    k3 = p1.vert.co - off1 - off2                 
                    vmap[p1] = ['b', (k1, k2, k3)]
                else:
                    vmap[p1] = ['c', co3]
                    pass
            else:                
                leng1 = p1.link_loop_next.vert.co - p1.vert.co
                leng2 = p1.link_loop_prev.vert.co - p1.vert.co
                off1 = m1.normalized() * min(plen, leng1.length * 0.4)
                off2 = m2.normalized() * min(plen, leng2.length * 0.4)
                k1 = p1.vert.co + off1
                k2 = p1.vert.co + off2
                e1 = p1.edge
                e2 = p1.link_loop_prev.edge
                v1, v2 = self.chop_edge(bm, [e1, e2], [k1, k2])
                vmap[p1] = ['a', co3]        

        for p1 in vmap:
            bag = vmap[p1]
            t, item = bag
            if t == 'a':                
                v1 = bm.verts.new(item)
                bag[1] = v1
            elif t == 'b':
                a, b, c = item
                v1 = bm.verts.new(a)
                v2 = bm.verts.new(b)
                v3 = bm.verts.new(c)
                bag[1] = (v1,v2,v3)
            elif t == 'c':
                v1 = bm.verts.new(item)
                bag[1] = v1

        coss2 = coss[1:] + [coss[0]]
        for co, co2 in zip(coss, coss2):
            p1 = None
            pn = None
            for p2 in f1.loops:
                if p2.vert.co == co:
                    p1 = p2
                if p2.vert.co == co2:
                    pn = p2
            if p1 == None or pn == None:
                break

            sides = []
            t1, item1 = vmap[p1]
            t2, item2 = vmap[pn]

            if t1 == 'b':                
                k1, k2, k3 = item1
                f2 = bm.faces.new((p1.vert, k1, k3, k2))
                f2.normal_update()         
                fss.append(f2)
                sides.append((p1.vert, k1)) 
                inner1.append(k2)   
                inner1.append(k3)
                inner1.append(k1)            
            elif t1 == 'c':
                v3 = item1
                sides.append((p1.vert, v3))   
                inner1.append(v3)             
            elif t1 == 'a':
                v3 = item1
                v1 = p1.link_loop_next.vert
                v2 = p1.link_loop_prev.vert
                f2 = bm.faces.new((p1.vert, v1, v3, v2))
                f2.normal_update()
                fss.append(f2)
                sides.append((v1, v3))
                inner1.append(v3) 

            if t2 == 'b':                
                k1, k2, k3 = item2
                sides.append((pn.vert, k2)) 
            elif t2 == 'c':
                v3 = item2
                sides.append((pn.vert, v3)) 
            elif t2 == 'a':
                v3 = item2
                v1 = pn.link_loop_next.vert
                v2 = pn.link_loop_prev.vert
                sides.append((v2, v3))
            
            (a, b), (c, d) = sides     
            f3 = bm.faces.new((a, c, d, b))
            f3.normal_update()      
            fss.append(f3)   

        finner = bm.faces.new(inner1)
        finner.normal_update()

        bmesh.ops.delete(bm, geom=[f1], context='FACES')        
        return finner, fss


    def chop_line(self, bm, v1, v2):
        res = bmesh.ops.connect_verts(bm, verts=[v1, v2])
        es = res['edges']
        if len(es) == 0:
            return None
        return es[0]


    def chop_edge(self, bm, es, cs):
        res = bmesh.ops.bisect_edges(bm, edges=es, cuts=1)
        vs = [e for e in res['geom_split'] if isinstance(e, bmesh.types.BMVert)]
        for v, co in zip(vs, cs):
            v.co = co
        return vs


    def get_excluded(self, bm, fss):
        excluded = set(bm.faces) - fss
        return excluded


    def sub_div(self, bm, excluded):
        cuts = self.cuts
        fs2 = []
        esall = set()
        remaining = set(bm.faces) - excluded

        for f1 in remaining:
            es = f1.edges            
            esall = esall.union(set(es))
            if len(es) != 4:
                fs2.append(f1)            

        bmesh.ops.subdivide_edges(bm, edges=list(esall), 
            cuts=1, use_grid_fill=True, use_only_quads=True)
    

        for f1 in fs2:
            cen = f1.calc_center_median()
            v1 = bm.verts.new(cen)            
            for i, p in enumerate(f1.loops):
                if i % 2 == 1:
                    p2 = p.link_loop_next
                    p3 = p2.link_loop_next
                    vs = [v1, p.vert, p2.vert, p3.vert]                    
                    f2 = bm.faces.new(vs)                
                    f2.normal_update()
        
        bmesh.ops.delete(bm, geom=fs2, context='FACES')

        remaining = set(bm.faces) - excluded
        esall2 = set()
        for f1 in remaining:
            esall2 = esall2.union(set(f1.edges))
        esall2 = list(esall2)            

        cuts = cuts - 1
        if cuts > 0:        
            bmesh.ops.subdivide_edges(bm, edges=esall2, 
                cuts=cuts, use_grid_fill=True, use_only_quads=True)

                


    def process_smooth(self, bm, excluded):
        inners = set()
        bounding = set()
        # for v1 in bm.verts:
        #     bound = any([e1.is_boundary for e1 in v1.link_edges])                
        #     if bound == False:
        #         inners.append(v1)
        keep = self.prop_keep_edge
        keepangle = self.prop_keep_edge_angle

        remaining = set(bm.faces) - excluded
        for f1 in remaining:
            bound = False
            for e1 in f1.edges:
                if e1.is_boundary:                    
                    bound = True
                    break

                if keep:
                    if len(e1.link_faces) == 2:
                        d1 = e1.calc_face_angle()                        
                        if d1 > math.radians(keepangle):
                            bound = True
                            break
                for f2 in e1.link_faces:
                    if f2 in excluded:                        
                        bound = True
                        break
            if bound:
                for v1 in f1.verts:
                    bounding.add(v1)
            else:
                for v1 in f1.verts:
                    inners.add(v1)
        
        inners = inners - bounding
        inners = list(inners)
        
        self.smoothing(inners)
        




    def smoothing(self, vs):
        vmap = {}
        keep = self.prop_keep_edge
        for v1 in vs:            
            cs = []
            for f1 in v1.link_faces:
                cen = f1.calc_center_median()
                cs.append(cen)
            vmap[v1] = cs

        for v1 in vmap:
            p1 = Vector()
            cs = vmap[v1]
            for c1 in cs:
                p1 = p1 + c1
            p1 = p1 / len(cs)   

            if keep:
                m1 = p1 - v1.co
                pro1 = m1.project(v1.normal)
                v1.co = p1 - pro1
            else:
                v1.co = p1
            # pint = self.overflow(v1, p1)            
            # if pint == False:
            #     v1.co = p1
            # else:
            #     m1 = pint - v1.co
            #     v1.co = v1.co + m1 * 0.5


    def overflow(self, v1, p1):
        es = set()
        es2 = set()
        for f1 in v1.link_faces:
            for e1 in f1.edges:
                es.add(e1)
        for e1 in v1.link_edges:
            es2.add(e1)
        es3 = es - es2
        for e1 in es3:
            a, b = e1.verts
            p2 = (p1 - v1.co) * 2 + v1.co
            res = self.get_cross_inside(v1.co, p2, a.co, b.co)
            if res != None:
                return res
        return False


    def inside(self, p1, v1, v2):
        m1 = p1 - v1
        m2 = p1 - v2
        m3 = v2 - v1
        if (m1.length + m2.length) - m3.length < 0.001:
            return True
        else:
            return False



    def get_cross_inside(self, v1, v2, v3, v4):
        res = mathutils.geometry.intersect_line_line(v1, v2, v3, v4)        
        if res == None:
            return None
        p1, p2 = res        
        if (p2 - p1).length < 0.001:
            if self.inside(p1, v1, v2) and self.inside(p1, v3, v4):
                return p1
        else:
            return None
    


    def inseting2(self, vs, bm, f1):     
        plen = self.plen
        sn = f1.normal
        vs2 = []        
        # vmap = {}
        # kvmap = {}
        fss = []
        for v1 in vs:
            m1 = v1.next.vert.co - v1.vert.co
            m2 = v1.prev.vert.co - v1.vert.co
            m3 = self.mid_line(m1, m2, sn)
            m3 = m3.normalized() * plen
            co = v1.vert.co + m3
            v2 = Vloop(co)
            vs2.append(v2)
            #
            if v1.is_concave(sn):
                if v1.angle() < math.radians(120):
                    leng1 = v1.next.vert.co - v1.vert.co
                    leng2 = v1.prev.vert.co - v1.vert.co
                    off1 = m2.normalized() * min(plen, leng1.length * 0.4)
                    off2 = m1.normalized() * min(plen, leng2.length * 0.4)
                    k1 = v1.vert.co - off1
                    k2 = v1.vert.co - off2
                    vk1 = Vloop(k1)
                    vk2 = Vloop(k2)
                    # vmap[v1] = ['c', v2, vk1, vk2]   
                    v1.ptype = 'c'
                    v1.v2 = v2
                    v2.co = v1.vert.co - off1 - off2
                    v1.vk1 = vk1
                    v1.vk2 = vk2
                else:
                    # vmap[v1] = ['b', v2]
                    v1.ptype = 'b'
                    v1.v2 = v2
            else:                
                leng1 = v1.next.vert.co - v1.vert.co
                leng2 = v1.prev.vert.co - v1.vert.co
                k1 = v1.vert.co + m1.normalized() * min(plen, leng1.length * 0.4)
                k2 = v1.vert.co + m2.normalized() * min(plen, leng2.length * 0.4)
                vk1 = Vloop(k1)
                vk2 = Vloop(k2)
                # vmap[v1] = ['a', v2, vk1, vk2]
                v1.ptype = 'a'
                v1.v2 = v2
                v1.vk1 = vk1
                v1.vk2 = vk2                
        self.link_all(vs2)       
        pvs1 = []        
        for v1 in vs:            
            if v1.ptype == 'a':
                v1.pv1 = bm.verts.new(v1.vert.co)  
                v1.pv2 = bm.verts.new(v1.v2.vert.co)
                v1.pvk1 = bm.verts.new(v1.vk1.vert.co)
                v1.pvk2 = bm.verts.new(v1.vk2.vert.co)
                pvs1.append(v1.pv2)
            elif v1.ptype == 'c':
                v1.pv1 = bm.verts.new(v1.vert.co)  
                v1.pv2 = bm.verts.new(v1.v2.vert.co)
                v1.pvk1 = bm.verts.new(v1.vk1.vert.co)
                v1.pvk2 = bm.verts.new(v1.vk2.vert.co)
                pvs1.append(v1.pvk2)
                pvs1.append(v1.pv2)  
                pvs1.append(v1.pvk1)                
            elif v1.ptype == 'b':                
                v1.pv1 = bm.verts.new(v1.vert.co)
                v1.pv2 = bm.verts.new(v1.v2.vert.co)                
                pvs1.append(v1.pv2)                

        for v1 in vs:            
            vnext = v1.next
            sides = []
            if v1.ptype == 'a':                
                f3 = bm.faces.new([v1.pv1, v1.pvk1, v1.pv2, v1.pvk2])
                f3.normal_update()
                sides.append((v1.pvk1, v1.pv2))
                fss.append(f3)
            elif v1.ptype == 'c':                
                f3 = bm.faces.new([v1.pv1, v1.pvk1, v1.pv2, v1.pvk2])
                f3.normal_update()
                sides.append((v1.pv1, v1.pvk1))
                fss.append(f3)                
            elif v1.ptype == 'b':                
                sides.append((v1.pv1, v1.pv2))

            if vnext.ptype == 'a':                
                sides.append((vnext.pvk2, vnext.pv2))
            elif vnext.ptype == 'c':                
                sides.append((vnext.pv1, vnext.pvk2))
            elif vnext.ptype == 'b':                
                sides.append((vnext.pv1, vnext.pv2))

            pa, pb = sides[0]
            pc, pd = sides[1]
            f4 = bm.faces.new([pa, pc, pd, pb])
            f4.normal_update()
            fss.append(f4)

        f2 = bm.faces.new(pvs1)
        f2.normal_update()    
        #fss.append(f2)        
        # bmesh.ops.delete(bm, geom=[f1], context='FACES')        
        return f2, fss

       

    def shift(self, vs):
        vs2 = vs[1:] + [vs[0]]
        return zip(vs, vs2)
    

    def quad_fix(self, bm, f1):
        ct = len(f1.edges)
        if ct % 4 != 0:
            q1 = 4 - (ct % 4)
            for i in range(q1):
                ps = [(p.edge.calc_length(), p) for p in f1.loops]
                _, pm = max(ps, key=lambda e: e[0])
                self.cut_quad(bm, f1, pm)


    def cut_quad(self, bm, f1, pm, ct):
        f2 = self.near_face(f1, pm.edge)
        fp = self.loop_from_edge(f2, pm.edge)    
        fp2 = fp.link_loop_next.link_loop_next
        res1 = bmesh.ops.subdivide_edges(bm, edges=[pm.edge, fp2.edge], 
            cuts=ct, use_grid_fill=False)

                
    def loop_from_edge(self, f1, e1):
        for p in f1.loops:
            if p.edge == e1:
                return p
        return None


    def near_face(self, f1, e1):
        f2, f3 = e1.link_faces
        if f2 == f1:
            fp = f3
        else:
            fp = f2        
        return fp


    def is_concave(self, p, sn):
        m2 = p.vert.co - p.link_loop_prev.vert.co
        c1 = m2.cross(sn)
        m1 = p.link_loop_next.vert.co - p.vert.co

        if m1.cross(m2).length < 0.001:
            return False

        if c1.length == 0 or m1.length == 0:
            return False
        if c1.angle(m1) < math.radians(90):
            return True
        else:
            return False


    def is_crossed(self, p, p4, ft, fvm):
        a = fvm[p]
        b = fvm[p4]
        pmath = PlaneMath()
        for pn in ft.loops:
            pn2 = pn.link_loop_next            
            if p == pn or p4 == pn:
                continue
            if p == pn2 or p4 == pn2:
                continue
            c = fvm[pn]
            d = fvm[pn2]
            if pmath.is_inter(a, b, c, d):
                return True            
        return False


    def is_crossed_old(self, p, p4, ft):
        for pn in ft.loops:
            pn2 = pn.link_loop_next
            pn3 = pn.link_loop_prev
            if p == pn or p4 == pn:
                continue
            if p == pn2 or p4 == pn2:
                continue
            
            pin = self.get_cross_inside(p.vert.co, p4.vert.co, 
                pn.vert.co, pn2.vert.co)
            if pin != None:
                # self.draw_point(pin)
                return True       
        return False        


    def get_angles(self, p, pm):
        p2 = p.link_loop_next
        p3 = p.link_loop_prev
        m2 = p2.vert.co - p.vert.co
        m3 = p3.vert.co - p.vert.co
        m1 = pm.vert.co - p.vert.co
        if m1.length == 0 or m2.length == 0 or m3.length == 0:
            return 0, 0
        d1 = m1.angle(m2)
        d2 = m1.angle(m3)
        return d1, d2


    def cut_face(self, bm, v1, v2):
        res = bmesh.ops.connect_verts(bm, verts=[v1, v2])
        es = res['edges']
        if len(es) == 0:
            return None
        e1 = es[0]
        if len(e1.link_faces) != 2:
            return None
        efs = list(e1.link_faces)
        # self.even_cut_single(bm, e1)
        return efs




    def div_faces_base(self, bm, f1):     
        if len(f1.loops) <= 4:
            return [f1]

        self.even_cut_simple(bm, f1)
        # fvm = self.get_fvm(f1)

        d179 = math.radians(179)
        fcon = [p for p in f1.loops if p.is_convex == False and p.calc_angle() <= d179]
        if len(fcon) == 0:
            return [f1]

        for p in fcon:                     
            # ps = []            
            spt = None
            sdm = None            
            for p2 in f1.loops:
                if p == p2:
                    continue
                d1, d2 = self.get_angles(p, p2)
                d3, d4 = self.get_angles(p2, p)
                # d90 = math.radians(90)
                # dm = abs(d1-d90) + abs(d2-d90) + abs(d3-d90) + abs(d4-d90)
                dm = abs(d1-d2) + abs(d3-d4)                
                if sdm != None and dm > sdm:
                    continue

                d30 = math.radians(75)
                if d1 < d30 or d2 < d30:
                    continue
                if d3 < d30 or d4 < d30:
                    continue
                
                if self.get_real_angle_cmp(p, p2, f1.normal):
                    continue

                # if self.is_crossed(p, p2, f1, fvm):
                #     continue

                if self.is_crossed_old(p, p2, f1):
                    continue                

                # d1, d2 = self.get_real_angle(p, p2, f1.normal)
                # if d1 < d2:
                #     continue           
                
                # ps.append((dm, p2))
                if sdm == None or dm < sdm:
                    sdm = dm
                    spt = p2              

            #_, pm = min(ps, key=lambda e:e[0])
            # ps2 = [e for e in ps if (e[1].vert in used) == False]
            
            # ps2 = ps
            # if len(ps2) == 0:
            #     continue        
            # _, pm = min(ps2, key=lambda e:e[0])  
            if spt == None:
                continue
            pm = spt

            # self.draw_point(pm.vert.co)            
            # used.add(pm.vert)
            # used.add(p.vert)
            # gui.lines += [p.vert.co, pm.vert.co]
            cf = self.cut_face(bm, p.vert, pm.vert)
            if cf == None:
                continue
            lencf = len(cf)
            if lencf == 0:
                continue
            elif lencf == 1:
                cf2 = self.div_faces_base(bm, cf[0])
                return cf2
            else:
                cf2 = self.div_faces_base(bm, cf[0])
                cf3 = self.div_faces_base(bm, cf[1])
                return cf2 + cf3
            # return cf
        return [f1]


 

    def div_faces_remain_4(self, bm, f1, count):
        # if count == 6:
        #     return
        d179 = math.radians(179)
        fcon = [p for p in f1.loops if p.is_convex == False and p.calc_angle() <= d179]
        if len(fcon) == 0:
            return
        p = fcon[0]
        m1 = p.link_loop_next.vert.co - p.vert.co
        m2 = p.link_loop_prev.vert.co - p.vert.co
        m3 = self.mid_line(m1, m2, f1.normal)
        k1 = p.vert.co + m3 * 1000
        
        kp1 = None        
        for p2 in f1.loops:
            if p2 == p:
                continue
            a = p2.vert.co
            b = p2.link_loop_next.vert.co
            pin = self.get_cross_inside(p.vert.co, k1, a, b)
            if pin != None:
                kp1 = (p2, pin)
                break

        if kp1 == None:
            return
        kp, pin = kp1
        rep = None

        for p2 in f1.loops:
            m1 = p2.vert.co - kp.vert.co
            if m1.length < self.plen * 2:
                rep = p2
                break

        if rep == None:
            res1 = bmesh.ops.subdivide_edges(bm, edges=[kp.edge], 
                cuts=1, use_grid_fill=False)
            g1 = res1['geom_inner']
            if len(g1) == 0:
                return
            v2 = g1[0]        
            v2.co = pin
        else:
            v2 = rep.vert
        fs = self.cut_face(bm, p.vert, v2)
        for f2 in fs:
            self.div_faces_remain(bm, f2, count + 1)




    def div_faces_remain_3(self, bm, f1):
        d179 = math.radians(179)
        fcon = [p for p in f1.loops if p.is_convex == False and p.calc_angle() <= d179]
        if len(fcon) == 0:
            return
        p = fcon[0]
        m1 = p.vert.co - p.link_loop_next.vert.co
        m2 = p.vert.co - p.link_loop_prev.vert.co
        k1 = p.vert.co + m1 * 1000
        k2 = p.vert.co + m2 * 1000
        kp1 = None
        kp2 = None
        for p2 in f1.loops:
            if p2 == p:
                continue
            a = p2.vert.co
            b = p2.link_loop_next.vert.co
            pin = self.get_cross_inside(p.vert.co, k1, a, b)
            if pin != None:
                kp1 = (p2, pin)
                break
        for p2 in f1.loops:
            if p2 == p:
                continue            
            a = p2.vert.co
            b = p2.link_loop_next.vert.co
            pin = self.get_cross_inside(p.vert.co, k2, a, b)
            if pin != None:
                kp2 = (p2, pin)
                break         
        if kp1[0].edge.calc_length() > kp2[0].edge.calc_length():
            kp, pin = kp1
        else:
            kp, pin = kp2

        res1 = bmesh.ops.subdivide_edges(bm, edges=[kp.edge], 
            cuts=1, use_grid_fill=False)
        g1 = res1['geom_inner']
        if len(g1) == 0:
            return
        v2 = g1[0]
        v2.co = pin
        fs = self.cut_face(bm, p.vert, v2)
        for f2 in fs:
            self.div_faces_remain(bm, f2)

                

    def div_faces_remain(self, bm, f1, used=None):
        if used == None:
            used = set()
        if len(f1.loops) <= 3:
            return [f1]

        # self.even_cut_simple(bm, f1)

        d179 = math.radians(179)
        fcon = [p for p in f1.loops if p.is_convex == False and p.calc_angle() <= d179]
        if len(fcon) == 0:
            return [f1]

        for p in fcon:                     
            ps = []
            for p2 in f1.loops:
                if p == p2:
                    continue
                d1, d2 = self.get_angles(p, p2)
                d3, d4 = self.get_angles(p2, p)
                # d90 = math.radians(90)
                # dm = abs(d1-d90) + abs(d2-d90) + abs(d3-d90) + abs(d4-d90)
                dm = abs(d1-d2) + abs(d3-d4)
                d30 = math.radians(1)
                if d1 < d30 or d2 < d30:
                    continue
                if d3 < d30 or d4 < d30:
                    continue
                if self.is_crossed(p, p2, f1):
                    continue

                d1, d2 = self.get_real_angle(p, p2, f1.normal)
                if d1 < d2:
                    continue              
                ps.append((dm, p2))
            #_, pm = min(ps, key=lambda e:e[0])
            # ps2 = [e for e in ps if (e[1].vert in used) == False]
            ps2 = ps

            if len(ps2) == 0:
                continue
            # print('total', len(f1.loops))
            # print(len(ps2), len(ps3))            
            _, pm = min(ps2, key=lambda e:e[0])            
            # self.draw_point(pm.vert.co)            
            # used.add(pm.vert)
            # used.add(p.vert)
            # gui.lines += [p.vert.co, pm.vert.co]
            cf = self.cut_face(bm, p.vert, pm.vert)
            cf2 = self.div_faces_remain(bm, cf[0], used)
            cf3 = self.div_faces_remain(bm, cf[1], used)
            return cf2 + cf3
            # return cf
        return [f1]




    def div_faces_simple_2(self, bm, f1, used=None):
        if used == None:
            used = set()
        if len(f1.loops) <= 4:
            return [f1]

        self.even_cut_simple(bm, f1)

        d179 = math.radians(179)
        fcon = [p for p in f1.loops if p.is_convex == False and p.calc_angle() <= d179]
        if len(fcon) == 0:
            return [f1]

        for p in fcon:                     
            ps = []
            for p2 in f1.loops:
                if p == p2:
                    continue
                d1, d2 = self.get_angles(p, p2)
                d3, d4 = self.get_angles(p2, p)
                # d90 = math.radians(90)
                # dm = abs(d1-d90) + abs(d2-d90) + abs(d3-d90) + abs(d4-d90)
                dm = abs(d1-d2) + abs(d3-d4)
                d30 = math.radians(30)
                if d1 < d30 or d2 < d30:
                    continue
                if d3 < d30 or d4 < d30:
                    continue
                if self.is_crossed(p, p2, f1):
                    continue

                d1, d2 = self.get_real_angle(p, p2, f1.normal)
                if d1 < d2:
                    continue              
                ps.append((dm, p2))
            #_, pm = min(ps, key=lambda e:e[0])
            ps2 = [e for e in ps if (e[1].vert in used) == False]

            if len(ps2) == 0:
                continue
            # print('total', len(f1.loops))
            # print(len(ps2), len(ps3))            
            _, pm = min(ps2, key=lambda e:e[0])            
            # self.draw_point(pm.vert.co)            
            used.add(pm.vert)
            used.add(p.vert)
            # gui.lines += [p.vert.co, pm.vert.co]
            cf = self.cut_face(bm, p.vert, pm.vert)
            cf2 = self.div_faces_simple(bm, cf[0], used)
            cf3 = self.div_faces_simple(bm, cf[1], used)
            return cf2 + cf3
            # return cf
        return [f1]


    def get_count(self, p1, p2, f1):
        i = 0
        s1 = 0
        s2 = 0
        for p in f1.loops:            
            if p == p1:
                s1 = i
            if p == p2:
                s2 = i
            i += 1
        return abs(s1 - s2)



    def get_fvm(self, f1):
        v1 = f1.verts[0]
        v2 = f1.verts[1]
        m1 = v2.co - v1.co
        sn = f1.normal
        vm = self.get_matrix(m1, sn.cross(m1), sn, v1.co)
        #return vm.inverted()
        fvm = {}
        for p in f1.loops:            
            fvm[p] = vm @ p.vert.co
        return fvm


    def div_faces_quad(self, bm, f1):
        if len(f1.loops) <= 4:
            return [f1]

        self.even_cut_simple(bm, f1)
        # fvm = self.get_fvm(f1)
        # d179 = math.radians(179)
        # fcon = [p for p in f1.loops if p.is_convex == False and p.calc_angle() <= d179]
        # if len(fcon) == 0:
        #     return [f1]
        # ps = []
        spt = None
        sdm = None
        for i1, p in enumerate(f1.loops):
            # if p.vert in used:
            #     continue
            for i2, p2 in enumerate(f1.loops):
                if p == p2:
                    continue
                if i1 > i2:
                    continue
                # if self.get_count(p, p2, f1) < 3:
                #     continue
                # if p2.vert in used:
                #     continue
                d1, d2 = self.get_angles(p, p2)
                d3, d4 = self.get_angles(p2, p)
                d90 = math.radians(90)
                dm = abs(d1-d90) + abs(d2-d90) + abs(d3-d90) + abs(d4-d90)
                if sdm != None and dm > sdm:
                    continue
                # dm = abs(d1-d2) + abs(d3-d4)
                d30 = math.radians(30)
                if d1 < d30 or d2 < d30:
                    continue
                if d3 < d30 or d4 < d30:
                    continue                

                # d1, d2 = self.get_real_angle_cmp(p, p2, f1.normal)
                # if d1 < d2:
                #     continue                

                if self.get_real_angle_cmp(p, p2, f1.normal):
                    continue

                # if self.is_crossed(p, p2, f1, fvm):
                #     continue

                if self.is_crossed_old(p, p2, f1):
                    continue                

                # short1 = self.get_shortest(p, p2, f1)
                # if short1 < self.plen * 2:
                #     continue
                
                # ps.append((dm, (p, p2)))
                if sdm == None or dm < sdm:
                    sdm = dm
                    spt = (p, p2)

        #_, pm = min(ps, key=lambda e:e[0])
        # print('total', len(f1.loops))
        # print(len(ps2), len(ps3))            
        
        # if len(ps) == 0:
        #     return [f1]
        # _, pt = min(ps, key=lambda e:e[0])            
        # p, pm = pt
        if spt == None:
            return [f1]
        p, pm = spt

        # self.draw_point(pm.vert.co)            
        # used.add(pm.vert)
        # used.add(p.vert)
        # gui.lines += [p.vert.co, pm.vert.co]
        cf = self.cut_face(bm, p.vert, pm.vert)
        if cf == None:
            return [f1]
        lencf = len(cf)
        if lencf == 0:
            return [f1]
        elif lencf == 1:
            cf2 = self.div_faces_quad(bm, cf[0])
            return cf2
        else:
            cf2 = self.div_faces_quad(bm, cf[0])
            cf3 = self.div_faces_quad(bm, cf[1])
            return cf2 + cf3        
        # cf2 = self.div_faces_quad(bm, cf[0])
        # cf3 = self.div_faces_quad(bm, cf[1])
        # return cf2 + cf3
            # return cf
        # return [f1]



    def get_shortest(self, p, p2, f1):        
        sn = f1.normal
        m1 = p2.vert.co - p.vert.co
        vm = self.get_matrix(m1, sn.cross(m1), sn, p.vert.co)
        vm2 = vm.inverted()
        ms = []
        for p3 in f1.loops:
            if p3 == p or p3 == p2:
                continue
            if p3.link_loop_next == p or p3.link_loop_next == p2:
                continue
            k1 = vm2 @ p3.vert.co
            k2 = vm2 @ p3.link_loop_next.vert.co
            ms.append(abs(k1.y))
            ms.append(abs(k2.y))
        return min(ms, key=lambda e:e)
           


    def div_faces_quad_old(self, bm, fsall):        
        fss2 = []
        used = set()
        for f1 in fsall:
            ft = f1
            while True:
                if len(ft.edges) <= 4:
                    fss2.append(ft)
                    break
                ps = []
                for p in ft.loops:
                    if p.vert in used:
                        continue
                    for p4 in ft.loops:    
                        if p == p4:
                            continue                
                        if p4.vert in used:
                            continue
                        d1, d2 = self.get_angles(p, p4)
                        d3, d4 = self.get_angles(p4, p)                    
                        d90 = math.radians(90)
                        dm = abs(d1-d90) + abs(d2-d90) + abs(d3-d90) + abs(d4-d90)                    
                        d30 = math.radians(30)
                        if d1 < d30 or d2 < d30:
                            continue
                        if d3 < d30 or d4 < d30:
                            continue
                        if self.is_crossed(p, p4, ft):
                            continue

                        d1, d2 = self.get_real_angle(p, p4, ft.normal)
                        if d1 >= 0:
                            if d1 <= d2:
                                continue
                        else:
                            if d2 <= d1:
                                continue

                        ps.append((dm, (p, p4)))
                # ps3 = []
                if len(ps) == 0:
                    break                    
                _, pm = min(ps, key=lambda e:e[0])
                p, p4 = pm       
                res = bmesh.ops.connect_verts(bm, verts=[p.vert, p4.vert])
                used.add(p.vert)
                used.add(p4.vert)                
                
                es = res['edges']
                if len(es) == 1:
                    e1 = es[0]
                    fs = list(e1.link_faces)
                    q1 = None
                    for f2 in fs:
                        if len(f2.edges) == 4:
                            fss2.append(f2)
                            q1 = f2                 
                    if q1 == None:
                        break
                    fs.remove(q1)
                    ft = fs[0]
                else:
                    break
        return fss2        



    def get_real_angle_cmp(self, p, pm, sn):
        p3 = p.link_loop_next
        m1 = p3.vert.co - p.vert.co
        vm = self.get_matrix(m1, sn.cross(m1), sn, p.vert.co)
        vm2 = vm.inverted()        
        vp = vm2 @ pm.vert.co
        return vp.y < 0




    def get_real_angle(self, p, pm, sn):
        p2 = p.link_loop_prev
        m1 = p2.vert.co - p.vert.co
        vm = self.get_matrix(m1, sn.cross(m1), sn, p.vert.co)
        vm2 = vm.inverted()
        p3 = p.link_loop_next
        vp = vm2 @ pm.vert.co
        deg = math.atan2(vp.y, vp.x)        
        if deg < 0:
            deg += math.radians(360)
        vp2 = vm2 @ p3.vert.co
        deg2 = math.atan2(vp2.y, vp2.x)        
        if deg2 < 0:
            deg2 += math.radians(360)        
        return abs(deg), abs(deg2)


    
    def get_matrix(self, m1, m2, m3, cen):
        if m1.length == 0 or m2.length == 0 or m3.length == 0:
            return Matrix.Identity(4)            
        m = Matrix.Identity(4)        
        m[0][0:3] = m1.normalized()
        m[1][0:3] = m2.normalized()
        m[2][0:3] = m3.normalized()
        m[3][0:3] = cen.copy()
        m = m.transposed()
        return m    

    
    def div_faces_simple4(self, bm, f1):  
        if len(f1.loops) <= 4:
            return [f1]
        d179 = math.radians(179)
        fcon = [p for p in f1.loops if p.is_convex == False and p.calc_angle() < d179]
        if len(fcon) == 0:
            return [f1]

        cuts = []
        used = set()
        for p in fcon:
            ps = []
            for p2 in f1.loops:
                if p == p2:
                    continue
                d1, d2 = self.get_angles(p, p2)
                d3, d4 = self.get_angles(p2, p)
                d90 = math.radians(90)
                dm = abs(d1-d90) + abs(d2-d90) + abs(d3-d90) + abs(d4-d90)
                ps.append((dm, p2))
            #_, pm = min(ps, key=lambda e:e[0])
            ps2 = [e for e in ps if (e[1] in used) == False]            

            if len(ps2) == 0:
                continue
            _, pm = min(ps2, key=lambda e:e[0])
            cuts.append((p, pm))
            used.add(pm)
            used.add(p)
            # cf = self.cut_face(bm, p, pm)
            # cf2 = self.div_faces_simple(bm, cf[0])
            # cf3 = self.div_faces_simple(bm, cf[1])
            # return cf2 + cf3
        for a, b in cuts:
            gui.lines += [a.vert.co, b.vert.co]
            
        return [f1]





    def even_cut_simple(self, bm, f1):
        partlen = self.part
        es = []
        for p in f1.loops:
            mlen = p.edge.calc_length()
            if mlen > partlen:
                ct = math.ceil(mlen / partlen) - 1
                es.append((p.edge, ct))
        
        for e1, ct in es:
            res1 = bmesh.ops.subdivide_edges(bm, edges=[e1], 
                cuts=ct, use_grid_fill=False)        
            # bmesh.ops.bisect_edges(bm, edges=[e1], cuts=ct)



    def even_cut_single(self, bm, e1):
        partlen = self.part
        mlen = e1.calc_length()
        if mlen > partlen:
            ct = math.ceil(mlen / partlen) - 1            
            res1 = bmesh.ops.subdivide_edges(bm, edges=[e1], 
                cuts=ct, use_grid_fill=False)        
            # bmesh.ops.bisect_edges(bm, edges=[e1], cuts=ct)


    def even_cut(self, bm, f1):
        partlen = self.part
        for p in f1.loops:
            mlen = p.edge.calc_length()
            if mlen > partlen:
                ct = math.ceil(mlen / partlen) - 1
                self.cut_quad(bm, f1, p, ct)


    def div_faces_4(self, bm, f1):
        fss2 = []
        ft = f1
        num = 1
        while True:
            if len(ft.edges) <= 4:
                fss2.append(ft)
                break
            ps = []
            for p in ft.loops:
                p2 = p.link_loop_next
                p3 = p2.link_loop_next
                p4 = p3.link_loop_next
                p2b = p.link_loop_prev
                p4b = p4.link_loop_next
                m1 = p4.vert.co - p.vert.co
                m2 = p2.vert.co - p.vert.co
                m2b = p2b.vert.co - p.vert.co
                deg = m1.angle(m2)
                degb = m1.angle(m2b)
                m3 = p.vert.co - p4.vert.co
                m4 = p3.vert.co - p4.vert.co                
                m4b = p4b.vert.co - p4.vert.co
                deg2 = m3.angle(m4)
                deg2b = m3.angle(m4b)                
                dif = abs(deg - math.radians(90)) + abs(deg2 - math.radians(90))
                dif2 = abs(degb - math.radians(90)) + abs(deg2b - math.radians(90))
                if self.is_crossed(p, p4, ft):
                    print('crossed')
                    dif += 1000                

                ps.append((dif + dif2, p))
            _, pm = min(ps, key=lambda e:e[0])
            p = pm
            p2 = p.link_loop_next
            p3 = p2.link_loop_next
            p4 = p3.link_loop_next        
            res = bmesh.ops.connect_verts(bm, verts=[p.vert, p4.vert])  
            
            es = res['edges']
            if len(es) == 1:
                e1 = es[0]
                fs = list(e1.link_faces)
                q1 = None
                for f2 in fs:
                    if len(f2.edges) == 4:
                        fss2.append(f2)
                        q1 = f2                 
                if q1 == None:
                    break
                fs.remove(q1)
                ft = fs[0]
            else:
                break
        return fss2



    def div_faces_simple2(self, bm, f1):
        fss2 = []
        ft = f1
        num = 1
        while True:
            if len(ft.edges) <= 4:
                fss2.append(ft)
                break
            ps = []
            for p in ft.loops:
                p2 = p.link_loop_next
                p3 = p2.link_loop_next
                p4 = p3.link_loop_next
                m1 = (p.vert.co - p2.vert.co).length
                m2 = (p2.vert.co - p3.vert.co).length
                m3 = (p3.vert.co - p4.vert.co).length
                m4 = (p4.vert.co - p.vert.co).length
                avg = (m1 + m2 + m3 + m4)/4
                dif = abs(m1-avg) + abs(m2-avg) + abs(m3-avg) + abs(m4-avg)
                
                if self.is_concave(p, ft.normal):
                    if num == 2:
                        self.draw_point(p.vert.co)
                    pass
                else:
                    dif += 100
                ps.append((dif, p))
            _, pm = min(ps, key=lambda e:e[0])
            p = pm
            p2 = p.link_loop_next
            p3 = p2.link_loop_next
            p4 = p3.link_loop_next        
            res = bmesh.ops.connect_verts(bm, verts=[p.vert, p4.vert])  
            
            if num == 2:
                gui.addtext(p.vert.co, str(num))
                gui.addtext(p2.vert.co, str(num))
                gui.addtext(p3.vert.co, str(num))
                gui.addtext(p4.vert.co, str(num))
            num+=1
            es = res['edges']
            if len(es) == 1:
                e1 = es[0]
                fs = list(e1.link_faces)
                q1 = None
                for f2 in fs:
                    if len(f2.edges) == 4:
                        fss2.append(f2)
                        q1 = f2                 
                if q1 == None:
                    break
                fs.remove(q1)
                ft = fs[0]
            else:
                break
        return fss2




    def div_faces(self, bm, f1):
        fs = self.dividing(bm, f1)
        if len(fs) == 0:
            return []
        else:
            f2, f3 = fs
            fs2 = self.div_faces(bm, f2)
            fs3 = self.div_faces(bm, f3)
            if len(fs2) == 0:
                fs2 = [f2]
            if len(fs3) == 0:
                fs3 = [f3]
            return fs2 + fs3


    def dividing(self, bm, f1):
        fs2 = [p for p in f1.loops if p.is_convex == False]
        if len(fs2) == 0:
            return []        
        p = fs2[0]
        p2 = p.link_loop_next
        p3 = p.link_loop_prev
        m1 = p2.vert.co - p.vert.co
        m2 = p3.vert.co - p.vert.co
        m3 = self.mid_line(m1, m2, f1.normal)

        ds = []
        for k in f1.loops:
            if k == p or k == p2 or k == p3 or \
                k == p2.link_loop_next or k == p3.link_loop_prev:
                continue
            m4 = k.vert.co - p.vert.co
            if m4.length == 0:
                continue
            deg = m4.angle(m3)
            ds.append((deg, k))
        if len(ds) == 0:
            return []
        
        _, k1 = min(ds, key=lambda e: e[0])

        res = bmesh.ops.connect_verts(bm, verts=[p.vert, k1.vert])
        es = res['edges']        
        if len(es) > 0:
            e1 = es[0]
            fs = list(e1.link_faces)
            return fs
        else:
            return []



    def mid_line(self, m1, m2, sn):
        fm1 = sn.cross(m1.normalized())
        fm2 = m2.normalized().cross(sn)
        m3 = (fm1 + fm2).normalized()
        return m3
       
    def execute(self, context):
        self.process(context)      
        return {'FINISHED'}    

    
    @classmethod
    def poll(cls, context):
        active_object = context.active_object
        selecting = active_object is not None and active_object.type == 'MESH'        
        editing = context.mode == 'EDIT_MESH' 
        is_vert_mode, is_edge_mode, is_face_mode = context.tool_settings.mesh_select_mode
        return selecting and editing 


    def invoke(self, context, event):
        if context.edit_object:

            self.prop_size_multiplier = 1.0

            self.process(context)
            return {'FINISHED'} 
        else:
            return {'CANCELLED'}


class PlaneMath:

    def is_inter(self, a, b, c, d):
        x1, y1,_ = a
        x2, y2,_ = b
        x3, y3,_ = c
        x4, y4,_ = d

        if ((x1 == x2 and y1 == y2) or (x3 == x4 and y3 == y4)):
            return False
        
        deno = ((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1))

        if (deno == 0):
            return False

        deno = deno * 1.0
        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / deno
        ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / deno

        if (ua < 0 or ua > 1 or ub < 0 or ub > 1):
            return False
        else:
            return True

    # def inter(self, a, b, c, d):
    #     x1, y1 = a
    #     x2, y2 = b
    #     x3, y3 = c
    #     x4, y4 = d

    #     if ((x1 == x2 and y1 == y2) or (x3 == x4 and y3 == y4)):
    #         return False
        
    #     deno = ((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1))

    #     if (deno == 0):
    #         return False

    #     deno = deno * 1.0

    #     ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / deno
    #     ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / deno

    #     if (ua < 0 or ua > 1 or ub < 0 or ub > 1):
    #         return False

    #     x = x1 + ua * (x2 - x1)
    #     y = y1 + ua * (y2 - y1)
    #     return (x, y)