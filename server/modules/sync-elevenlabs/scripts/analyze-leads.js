const sequelize = require('../config/database');
const LeadsService = require('../services/leadsService');

// ID del agente Ana Rodriguez
const ANA_AGENT_ID = 'agent_01jze991f4f92bbms2dbagk7yx';

async function analyzeLeads(agentId = null) {
  try {
    await sequelize.authenticate();
    console.log('✅ Conexión a la base de datos establecida');
    
    const leadsService = new LeadsService();
    
    // Mostrar leads efectivos
    await leadsService.showEffectiveLeads(agentId);
    
  } catch (error) {
    console.error('💥 Error en análisis de leads:', error.message);
    console.error(error.stack);
    process.exit(1);
  } finally {
    await sequelize.close();
    console.log('🔌 Conexión a la base de datos cerrada');
  }
}

// Función específica para Ana Rodriguez
async function analyzeAnaLeads() {
  console.log('🎯 Analizando leads de Ana Rodriguez...');
  return await analyzeLeads(ANA_AGENT_ID);
}

// Función para analizar todos los agentes
async function analyzeAllLeads() {
  console.log('🌍 Analizando leads de todos los agentes...');
  return await analyzeLeads();
}

if (require.main === module) {
  // Obtener argumentos de línea de comandos
  const args = process.argv.slice(2);
  
  if (args.length > 0) {
    const command = args[0].toLowerCase();
    
    switch (command) {
      case 'ana':
        analyzeAnaLeads();
        break;
      case 'all':
        analyzeAllLeads();
        break;
      default:
        // Si se proporciona un agent_id específico
        analyzeLeads(args[0]);
        break;
    }
  } else {
    // Por defecto, analizar leads de Ana
    analyzeAnaLeads();
  }
}

module.exports = { 
  analyzeLeads, 
  analyzeAnaLeads, 
  analyzeAllLeads 
};