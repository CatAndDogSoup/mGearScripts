"""Component Control 01 module"""

from mgear.shifter import component
from mgear.core import attribute, transform, primitive, applyop
from pymel.core import datatypes
import pymel.core as pm

#############################################
# COMPONENT
#############################################


class Component(component.Main):
    """Shifter component Class"""

    # =====================================================
    # OBJECTS
    # =====================================================
    def addObjects(self):
        """Add all the objects needed to create the component."""

        if self.settings["neutralRotation"]:
            t = transform.getTransformFromPos(self.guide.pos["root"])
        else:
            t = self.guide.tra["root"]
            if self.settings["mirrorBehaviour"] and self.negate:
                scl = [1, 1, -1]
            else:
                scl = [1, 1, 1]
            t = transform.setMatrixScale(t, scl)
        if self.settings["joint"] and self.settings["leafJoint"]:
            pm.displayInfo("Skipping ctl creation, just leaf joint")
            self.have_ctl = False
        else:
            self.have_ctl = True

            # we need to set the rotation order before lock any rotation axis
            if self.settings["k_ro"]:
                rotOderList = ["XYZ", "YZX", "ZXY", "XZY", "YXZ", "ZYX"]

            params = [
                s for s in ["tx", "ty", "tz", "ro", "rx", "ry", "rz", "sx", "sy", "sz"] if self.settings["k_" + s]
            ]

        if self.side == "L" or self.side == "C":
            ctl_one_x_matrix = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1]
        else:
            ctl_one_x_matrix = [-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1]

        self.ctl_size = 2

        t = transform.getTransformFromPos(self.guide.pos["hip"])
        self.ik_cns = primitive.addTransform(self.root, self.getName("hip_ik_cns"), t * ctl_one_x_matrix)

        self.hip = self.addCtl(
            parent=self.ik_cns,
            name="hip_ctl",
            m=t * ctl_one_x_matrix,
            color=self.color_ik,
            iconShape="cube",
            w=self.ctl_size,
            h=self.ctl_size,
            d=self.ctl_size,
        )

        t = transform.getTransformFromPos(self.guide.pos["paw"])
        self.ik_cns_ss = primitive.addTransform(
            self.root, self.getName("paw_ik_cns_ss"), [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1]
        )
        self.ik_cns = primitive.addTransform(self.ik_cns_ss, self.getName("paw_ik_cns"), t * ctl_one_x_matrix)
        self.paw = self.addCtl(
            parent=self.ik_cns,
            name="paw_ctl",
            m=t * ctl_one_x_matrix,
            color=self.color_ik,
            iconShape="cube",
            w=self.ctl_size,
            h=self.ctl_size,
            d=self.ctl_size,
        )

        t = transform.getTransformFromPos(self.guide.pos["paw"])
        self.ik_cns = primitive.addTransform(self.paw, self.getName("paw_rotate_ik_cns"), t * ctl_one_x_matrix)
        toffset = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -2, 0]
        self.paw_rotator_npo = primitive.addTransform(
            self.ik_cns, self.getName("paw_rotate_ik_npo"), t * ctl_one_x_matrix + toffset
        )
        self.paw_rotator = self.addCtl(
            parent=self.paw_rotator_npo,
            name="paw_rotator_ctl",
            m=t * ctl_one_x_matrix + toffset,
            color=self.color_ik,
            iconShape="cube",
            w=self.ctl_size * 0.5,
            h=self.ctl_size * 0.5,
            d=self.ctl_size * 0.5,
        )

        # POLE VECTOR
        t1 = self.guide.pos["knee"]
        t2 = self.guide.pos["ankle"]
        pos = [(t1[0] + t2[0]) / 2, (t1[1] + t2[1]) / 2, t2[2] - 5]
        t = transform.getTransformFromPos(pos)
        self.ik_cns = primitive.addTransform(self.root, self.getName("leg_pv_ik_cns"), t * ctl_one_x_matrix)
        self.pv_npo = primitive.addTransform(self.ik_cns, self.getName("leg_pv_ik_npo"), t * ctl_one_x_matrix)
        self.pv = self.addCtl(
            parent=self.pv_npo,
            name="leg_pv",
            m=t * ctl_one_x_matrix,
            color=self.color_ik,
            iconShape="null",
            w=self.ctl_size * 0.5,
            h=self.ctl_size * 0.5,
            d=self.ctl_size * 0.5,
        )

        ### DRIVER JOINTS
        driver_joints_vis = False
        self.hip_jnt = primitive.addJoint(
            self.root,
            self.getName("hip_driver"),
            transform.getTransformFromPos(self.guide.pos["hip"]),
            driver_joints_vis,
        )
        self.knee_jnt = primitive.addJoint(
            self.hip_jnt,
            self.getName("knee_driver"),
            transform.getTransformFromPos(self.guide.pos["knee"]),
            driver_joints_vis,
        )
        self.ankle_jnt = primitive.addJoint(
            self.knee_jnt,
            self.getName("ankle_driver"),
            transform.getTransformFromPos(self.guide.pos["ankle"]),
            driver_joints_vis,
        )
        self.paw_jnt = primitive.addJoint(
            self.ankle_jnt,
            self.getName("paw_driver"),
            transform.getTransformFromPos(self.guide.pos["paw"]),
            driver_joints_vis,
        )
        self.toe_jnt = primitive.addJoint(
            self.paw_jnt,
            self.getName("toe_driver"),
            transform.getTransformFromPos(self.guide.pos["toe"]),
            driver_joints_vis,
        )

        # IK JOINTS
        self.ik1_jnt = primitive.addJoint(
            self.root, self.getName("ik1"), transform.getTransformFromPos(self.guide.pos["hip"]), driver_joints_vis
        )
        pos = [(t1[0] + t2[0]) / 2, (t1[1] + t2[1]) / 2, t2[2] - 2]
        self.ik2_jnt = primitive.addJoint(
            self.ik1_jnt, self.getName("ik2"), transform.getTransformFromPos(pos), driver_joints_vis
        )
        self.ik3_jnt = primitive.addJoint(
            self.ik2_jnt, self.getName("ik3"), transform.getTransformFromPos(self.guide.pos["paw"]), driver_joints_vis
        )

        # REVERSE JOINTS
        self.rev1_jnt = primitive.addJoint(
            self.root, self.getName("rev1"), transform.getTransformFromPos(self.guide.pos["paw"]), driver_joints_vis
        )
        self.rev2_jnt = primitive.addJoint(
            self.rev1_jnt,
            self.getName("rev2"),
            transform.getTransformFromPos(self.guide.pos["ankle"]),
            driver_joints_vis,
        )

        ### DEFORMER JOINTS
        self.jnt_pos.append([self.hip_jnt, "hip", False])
        self.jnt_pos.append([self.knee_jnt, "knee", False])
        self.jnt_pos.append([self.ankle_jnt, "ankle", False])
        self.jnt_pos.append([self.paw_jnt, "paw", False])
        self.jnt_pos.append([self.toe_jnt, "toe", False])

        ### FUNCTION
        self.ik_ikh = primitive.addIkHandle(
            self.root, self.getName("ik_ikh"), [self.ik1_jnt, self.ik3_jnt], "ikRPsolver"
        )
        self.upleg_ikh = primitive.addIkHandle(
            self.root, self.getName("upleg_ikh"), [self.hip_jnt, self.ankle_jnt], "ikRPsolver"
        )
        self.downleg_ikh = primitive.addIkHandle(
            self.root, self.getName("downleg_ikh"), [self.ankle_jnt, self.paw_jnt], "ikSCsolver"
        )

    def addAttributes(self):
        # Ref
        if self.have_ctl:
            if self.settings["ikrefarray"]:
                ref_names = self.get_valid_alias_list(self.settings["ikrefarray"].split(","))
                if len(ref_names) > 1:
                    self.ikref_att = self.addAnimEnumParam("ikref", "Ik Ref", 0, ref_names)

    def addOperators(self):
        applyop.gear_matrix_cns(self.paw, self.ik_ikh)
        # Parent Constrain Paw control to downleg IKHandle
        applyop.gear_matrix_cns(self.paw, self.downleg_ikh)
        # Parent Constrain second reverse joint to upper leg IKHandle
        applyop.gear_matrix_cns(self.rev2_jnt, self.upleg_ikh)

        applyop.gear_matrix_cns(self.hip, self.hip_jnt)

        applyop.oriCns(self.ik3_jnt, self.paw_rotator_npo, maintainOffset=True)

        # Orient Constrain paw rotator control to reverse joint 1
        pm.pointConstraint(self.paw, self.rev1_jnt, maintainOffset=True)
        applyop.oriCns(self.paw_rotator, self.rev1_jnt, maintainOffset=True)
        # Orient Constrain paw control to paw jnt
        applyop.oriCns(self.paw, self.paw_jnt, maintainOffset=True)

        # applyop.gear_matrix_cns("global_C0_ctl", self.ik_cns_ss)
        pm.parentConstraint("global_C0_ctl", pm.PyNode(self.ik_cns_ss), maintainOffset=True)

        pm.poleVectorConstraint(pm.PyNode(self.pv), self.ik_ikh)
        pm.poleVectorConstraint(pm.PyNode(self.pv), self.upleg_ikh)

        pm.PyNode(self.upleg_ikh).twist.set(180)

        pv_pm = pm.PyNode(self.pv)
        paw_pm = pm.PyNode(self.paw)
        paw_rot_pm = pm.PyNode(self.paw_rotator)
        hip_pm = pm.PyNode(self.hip)

        for ctl_attr in [
            paw_pm.v, paw_pm.s,
            paw_rot_pm.v, paw_rot_pm.s, paw_rot_pm.t, paw_rot_pm.ry, paw_rot_pm.rz,
            hip_pm.v, hip_pm.t, hip_pm.r, hip_pm.s,
            pv_pm.v, pv_pm.r, pv_pm.s,
        ]:
            ctl_attr.lock()
            # ctl_attr.setKeyable(False)


    # =====================================================
    # CONNECTOR
    # =====================================================
    def setRelation(self):
        """Set the relation beetween object from guide to rig"""
        self.relatives["root"] = self.hip
        self.controlRelatives["root"] = self.hip

        self.relatives["paw"] = self.paw
        self.controlRelatives["paw"] = self.paw
        self.jointRelatives["paw"] = 4

        if self.settings["joint"]:
            self.jointRelatives["root"] = 0

        self.aliasRelatives["root"] = "ctl"

    def addConnection(self):
        """Add more connection definition to the set"""
        self.connections["standard"] = self.connect_standard
        self.connections["orientation"] = self.connect_orientation

    def connect_standard(self):
        """standard connection definition for the component"""
        self.connect_standardWithSimpleIkRef()

    def connect_orientation(self):
        """Orient connection definition for the component"""
        self.connect_orientCns()