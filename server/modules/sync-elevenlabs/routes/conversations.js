const express = require('express');
const ConversationController = require('../controllers/conversationController');

const router = express.Router();
const conversationController = new ConversationController();

// Sincronizar conversaciones desde ElevenLabs
router.post('/sync', (req, res) => conversationController.syncConversations(req, res));

// Obtener todos los agentes disponibles
router.get('/agents', (req, res) => conversationController.getAgents(req, res));

// Obtener conversaciones por nombre de agente
router.get('/agent/:agentName', (req, res) => conversationController.getConversationsByAgent(req, res));

// Obtener todas las conversaciones (con filtros opcionales)
router.get('/', (req, res) => conversationController.getConversations(req, res));

// Obtener conversación por ID
router.get('/:id', (req, res) => conversationController.getConversationById(req, res));

// Obtener audio de conversación
router.get('/:id/audio', (req, res) => conversationController.getConversationAudio(req, res));

module.exports = router;