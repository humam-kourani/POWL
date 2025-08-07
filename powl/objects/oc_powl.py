from powl.objects.obj import POWL


class OCPOWL:

    def __init__(self, powl_model: POWL, related, divergence, convergence, deficiency):
        self.powl_model = powl_model
        self.related = related
        self.divergence = divergence
        self.convergence = convergence
        self.deficiency = deficiency


