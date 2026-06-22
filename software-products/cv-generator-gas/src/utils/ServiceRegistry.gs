/**
 * @fileoverview Service accessor object for DeploymentIntegrity.check().
 *
 * Each property is a getter. The getter body runs when DeploymentIntegrity
 * reads SERVICES[entry.name] — i.e. at runtime inside check(), after every
 * .gs file has been parsed and every top-level var has been assigned.
 *
 * From the caller's perspective SERVICES is a plain static object:
 *   SERVICES['CvLogger']  →  the live CvLogger object, no () needed.
 *
 * Load-order independent: getter bodies are not evaluated at file-load time,
 * so the position of this file in the project makes no difference.
 *
 * To add a service: add a getter here AND add an entry to MANIFEST in
 * DeploymentIntegrity.gs.
 */
var SERVICES = {
  get TemplateBuilderService()  { return TemplateBuilderService;  },
  get CvGenerationService()     { return CvGenerationService;     },
  get SetupController()         { return SetupController;         },
  get TemplateEngine()          { return TemplateEngine;          },
  get DataAggregationService()  { return DataAggregationService;  },
  get CvLogger()                { return CvLogger;                },
  get ErrorHandler()            { return ErrorHandler;            },
};
