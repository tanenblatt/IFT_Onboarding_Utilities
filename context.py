from data_key import DataKey


class Context:
  def __init__(self):
    self.EventID                = None
    self.TransformationID       = None
    self.EventTime              = None
    self.TimeZone               = None
    self.Location               = None
    self.FromLocation           = None
    self.ToLocation             = None
    self.UnquantifiedItems      = None
    self.QuantifiedItems        = None
    self.UnquantifiedFromItems  = None
    self.QuantifiedFromItems    = None
    self.UnquantifiedToItems    = None
    self.QuantifiedToItems      = None
    self.ExpirationDate         = None
    self.SellByDate             = None
    self.BestBeforeDate         = None
    self.ReadPoint              = None
    self.Disposition            = None
    self.BizStep                = None
    self.PurchaseOrder          = None
    self.DespatchAdvice         = None
    self.ProductionOrder        = None
    self.SSCC                   = None
    self.Shipper                = None
    